import pandas as pd
from datetime import datetime
from scipy.stats import zscore
import os

# Zスコア分析を行い、指定したチームの試合からzscoreの高い（または低い）指標トップN件を抽出する関数
def generate_zscore_top_n(df, columns_to_analyze, team_row_index, top_n=10, threshold=1.3):
    df_z = df[columns_to_analyze].apply(zscore)
    z_row = df_z.loc[team_row_index].to_frame(name="zscore")
    z_row["abs_z"] = z_row["zscore"].abs()
    z_row = z_row[z_row["abs_z"] >= threshold].sort_values(by="abs_z", ascending=False).head(top_n)
    return [(metric, row["zscore"], "高め" if row["zscore"] > 0 else "低め") for metric, row in z_row.iterrows()]

# チームの勝ち試合を抽出し、その平均値と指定試合の値を比較するMarkdown表を生成する関数
def generate_win_pattern_table(df, team_name, match_row, key_metrics):
    win_rows = []
    for i in range(2, len(df)-1, 2):  # skip average rows
        team = df.iloc[i]
        opponent = df.iloc[i+1]
        if team["Team"] == team_name and team["Goals"] > opponent["Goals"]:
            win_rows.append(team)
        elif opponent["Team"] == team_name and opponent["Goals"] > team["Goals"]:
            win_rows.append(opponent)
    if not win_rows:
        return "⚠️ 勝利試合が見つかりませんでした。"

    win_df = pd.DataFrame(win_rows)
    numeric_cols = win_df.select_dtypes(include='number').columns
    win_avg = win_df[numeric_cols].mean()

    lines = ["| 指標 | 勝利試合平均 | 本試合 | 差 | コメント |",
             "|:------|---------------:|---------:|------:|:----------|"]
    
    #この指標は"🔼"、"🔽"が逆転
    reversed_metrics = {"PPDA", "Match tempo", "Average shot distance", "Shots against on target"}

    for col in key_metrics:
        try:
            win_val = float(win_avg[col])
            match_val = float(match_row[col])
            diff = match_val - win_val
            if col in reversed_metrics:
                arrow = "🔼" if diff < 0 else "🔽" if diff > 0 else "→"
            else:
                arrow = "🔼" if diff > 0 else "🔽" if diff < 0 else "→"
            lines.append(f"| {col} | {win_val:.2f} | {match_val:.2f} | {arrow} {diff:+.2f} | 【ここにLLMコメント】 |")
        except:
            continue
    return "\n".join(lines)

# Markdown形式の試合分析テンプレートを生成する関数
def generate_markdown_template(team_row, opponent_row, zscore_summary, win_pattern_table, match_date):
    def stat_line(metric):
        try:
            t, o = float(team_row[metric]), float(opponent_row[metric])
            diff = t - o
            reversed_metrics = {"PPDA", "Match tempo", "Average shot distance"}
            if metric in reversed_metrics:
                arrow = "🔼" if diff < 0 else "🔽" if diff > 0 else "→"
            else:
                arrow = "🔼" if diff > 0 else "🔽" if diff < 0 else "→"
            return f"| {metric} | {t:.2f} | {o:.2f} | {arrow} {diff:+.2f} |"
        except:
            return None


    key_metrics = ["xG", "PPDA", "Possession, %", "Match tempo",
                   "Average pass length", "Average shot distance","Goals",
                   "Shots on target","Positional attacks","Positional attacks with shots","Set pieces","Set pieces with shots","Corners","Corners with shots","Long passes","Long passes accurate%","Long pass %"]
    stats_lines = ["| 指標 | マリノス | 相手チーム | 差 |", "|:-----|---------:|-----------:|----:|"]
    stats_lines += [line for line in (stat_line(m) for m in key_metrics if m != "Goals") if line]

    zscore_lines = ["| 指標 | Zスコア | 傾向 | コメント |", "|:------|--------:|:------|:----------|"]
    zscore_lines += [f"| {m} | {z:+.2f} | {trend} | 【ここにLLMコメント】 |" for m, z, trend in zscore_summary]

    try:
        score_line = f"{team_row['Team']} {int(team_row['Goals'])} - {int(opponent_row['Goals'])} {opponent_row['Team']}（{match_date}）"
    except:
        score_line = f"{team_row['Team']} vs {opponent_row['Team']}（{match_date}）"

    return f"""
以下の試合データに基づき、次の出力をデータから読み取れる範囲のみで自然な日本語で記述してください。得点経過や印象を想像で補わず、スタッツの数値や差異に基づく記述のみとしてください。

1. 試合の要約（xG、得点、ポゼッション、PPDAなどスタッツから読み取れる範囲で3〜5行）
2. 改善ポイント（スタッツの低値や差から3行程度）
3. 明るい材料（ポジティブな指標から3行程度）
4. Zスコア指標上位5件へのコメント（1行ずつ）
5. 勝ちパターンとの比較から気づいたこと（数値差と傾向に基づき2〜3行）

noteにそのまま貼り付けができるよう、mdを穴埋めする形で生成をしてください
---
# ⚽ Jリーグ第X節｜{score_line}

## 🎯 試合概要
【要約をここに記入】

---

## 🆚 主要スタッツ比較

本試合におけるマリノスとXXの主要スタッツを比較します。

各指標は、チームの攻守における特徴やパフォーマンスを定量的に評価するためのものです。

{chr(10).join(stats_lines)}

---

## 🔍 Zスコア指標（上位5件）

Zスコアは「平均からどれだけ離れているか」を表す統計指標です。

- 正の値（＋）が大きいほど「平均より高い（多い）」
- 負の値（−）が大きいほど「平均より低い（少ない）」

このセクションでは、Zスコアが特に高い or 低い指標を抽出し、試合の特徴を浮き彫りにします。

{chr(10).join(zscore_lines)}

---

## 📊 勝ちパターンとの比較（平均）

この分析では、過去にマリノスが勝利した試合における平均値と、今回の試合のスタッツを比較しています。

- 各指標が「勝ったときの平均」と比べてどうだったか？
- どこが足りなかったのか？あるいは優れていたのか？

チームの勝利要因（パターン）を再確認するための参考になります。

{win_pattern_table}

---

## ⚠️ 改善ポイント
【改善ポイントをここに記入】

---

## ✅ 明るい材料
【明るい材料をここに記入】

---

## 🖊 総括
【要約を記者視点で記入】
"""

# レポート全体を実行してMarkdownを出力する関数
def generate_report(csv_path, output_path, match_date, team_name="Yokohama F. Marinos"):
    df = pd.read_csv(csv_path)
    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d", errors="coerce")
    df[columns_to_analyze] = df[columns_to_analyze].apply(pd.to_numeric, errors='coerce')

    match_df = df[df["Date"] == pd.to_datetime(match_date)]
    if match_df.empty:
        print("⚠️ 指定された日付の試合が見つかりません")
        return

    team_row = match_df[match_df["Team"] == team_name].iloc[0]
    opponent_row = match_df[match_df["Team"] != team_name].iloc[0]
    team_index = team_row.name

    zscore_summary = generate_zscore_top_n(df, columns_to_analyze, team_index)
    # 勝ちパターンとの比較で使う主要指標
    key_comparison_metrics = [
        "xG", "Shots on target", "Average shot distance",
        "Shots against on target",
        "Possession, %", "Passes accurate%",
        "PPDA", "Duels won%",
        "Positional attacks","Positional attacks with shots","Set pieces","Set pieces with shots","Corners","Corners with shots",
        "Long passes","Long passes accurate%","Long pass %"
    ]
    win_pattern_table = generate_win_pattern_table(df, team_name, team_row,key_comparison_metrics)
    md_text = generate_markdown_template(team_row, opponent_row, zscore_summary, win_pattern_table, match_date)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    print(f"✅ Markdown生成完了: {output_path}")

# 指標リスト（省略せず再利用可能な全指標）
columns_to_analyze = ['xG', 'Shots', 'Shots on target', 'Shots on target%', 'Passes', 'Passes accurate', 'Passes accurate%',
'Possession, %', 'Losses', 'Losses Low', 'Losses Medium', 'Losses High', 'Recoveries', 'Recoveries Low', 'Recoveries Medium',
'Recoveries High', 'Duels', 'Duels won', 'Duels won%', 'Shots from outside penalty area',
'Shots from outside penalty area on target', 'Shots from outside penalty area on target%', 'Positional attacks',
'Positional attacks with shots', 'Positional attacks with shots%', 'Counterattacks', 'Counterattacks with shots',
'Counterattacks with shots%', 'Set pieces', 'Set pieces with shots', 'Set pieces with shots%', 'Corners', 'Corners with shots',
'Corners with shots%', 'Free kicks', 'Free kicks with shots', 'Free kicks with shots%', 'Penalties', 'Penalties converted',
'Penalties converted%', 'Crosses', 'Crosses accurate', 'Crosses accurate%', 'Deep completed crosses', 'Deep completed passes',
'Penalty area entries (runs', 'Penalty area entries runs', 'Penalty area entries crosses', 'Touches in penalty area',
'Offensive duels', 'Offensive duels won', 'Offensive duels won%', 'Offsides', 'Conceded goals', 'Shots against',
'Shots against on target', 'Shots against on target%', 'Defensive duels', 'Defensive duels won', 'Defensive duels won%',
'Aerial duels', 'Aerial duels won', 'Aerial duels won%', 'Sliding tackles', 'Sliding tackles successful',
'Sliding tackles successful%', 'Interceptions', 'Clearances', 'Fouls', 'Yellow cards', 'Red cards', 'Forward passes',
'Forward passes accurate', 'Forward passes accurate%', 'Back passes', 'Back passes accurate', 'Back passes accurate%',
'Lateral passes', 'Lateral passes accurate', 'Lateral passes accurate%', 'Long passes', 'Long passes accurate',
'Long passes accurate%', 'Passes to final third', 'Passes to final third accurate', 'Passes to final third accurate%',
'Progressive passes', 'Progressive passes accurate', 'Progressive passes accurate%', 'Smart passes', 'Smart passes accurate',
'Smart passes accurate%', 'Throw ins', 'Throw ins accurate', 'Throw ins accurate%', 'Goal kicks', 'Match tempo',
'Average passes per possession', 'Long pass %', 'Average shot distance', 'Average pass length', 'PPDA']

# 実行部分（試合日付とファイルパスを指定）
if __name__ == "__main__":
    # 出力先ディレクトリが存在しない場合は作成
    output_dir = os.path.dirname("output/")
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    # Yokohama F. Marinosの試合データを指定してレポートを生成
    generate_report(
        csv_path="input/Team-Stats-Yokohama-F.-Marinos_arranged.csv",
        output_path="output/Yokohama-F_gpt_prompt.md",
        match_date="2025-08-09",
        team_name="Yokohama F. Marinos"
    )
