import pandas as pd

def arrange_headers_and_data(df):
    """
    DataFrameの1行目を複雑なヘッダーとして解釈し、分割・展開して分かりやすい列名に変換する関数。

    - 例: "Shots / on target" + 空欄2つ → ["Shots", "Shots on target", "Shots on target%"]
    - 例: "Losses / Low / Medium / High" + 空欄3つ → ["Losses", "Losses Low", "Losses Medium", "Losses High"]

    Args:
        df (pd.DataFrame): 1行目がヘッダー行になっているDataFrame（header=Noneで読み込んだもの）

    Returns:
        pd.DataFrame: 整形済みのDataFrame（1行目を新しいカラム名にし、2行目以降がデータ）
    """
    header_row = df.iloc[0].tolist()
    new_headers = []
    i = 0
    while i < len(header_row):
        current_header = str(header_row[i])
        if pd.isna(current_header) or current_header == "nan" or current_header == "":
            i += 1
            continue
        if "/" in current_header:
            parts = [part.strip() for part in current_header.split("/")]
            empty_count = 0
            j = i + 1
            while j < len(header_row) and (pd.isna(header_row[j]) or header_row[j] == "nan" or header_row[j] == ""):
                empty_count += 1
                j += 1
            main_part = parts[0]
            new_headers.append(main_part)
            if len(parts) == 2 and parts[1] == "on target":
                if empty_count == 2:
                    new_headers.append(f"{main_part} {parts[1]}")
                    new_headers.append(f"{main_part} {parts[1]}%")
                elif empty_count == 1:
                    new_headers.append(f"{main_part} {parts[1]}")
            elif len(parts) == 2 and parts[1] == "accurate":
                if empty_count == 2:
                    new_headers.append(f"{main_part} {parts[1]}")
                    new_headers.append(f"{main_part} {parts[1]}%")
                elif empty_count == 1:
                    new_headers.append(f"{main_part} {parts[1]}")
            elif len(parts) == 2 and parts[1] == "won":
                if empty_count == 2:
                    new_headers.append(f"{main_part} {parts[1]}")
                    new_headers.append(f"{main_part} {parts[1]}%")
                elif empty_count == 1:
                    new_headers.append(f"{main_part} {parts[1]}")
            elif len(parts) == 2 and parts[1] == "with shots":
                if empty_count == 2:
                    new_headers.append(f"{main_part} {parts[1]}")
                    new_headers.append(f"{main_part} {parts[1]}%")
                elif empty_count == 1:
                    new_headers.append(f"{main_part} {parts[1]}")
            elif len(parts) == 2 and parts[1] == "converted":
                if empty_count == 2:
                    new_headers.append(f"{main_part} {parts[1]}")
                    new_headers.append(f"{main_part} {parts[1]}%")
                elif empty_count == 1:
                    new_headers.append(f"{main_part} {parts[1]}")
            elif len(parts) == 2 and parts[1] == "successful":
                if empty_count == 2:
                    new_headers.append(f"{main_part} {parts[1]}")
                    new_headers.append(f"{main_part} {parts[1]}%")
                elif empty_count == 1:
                    new_headers.append(f"{main_part} {parts[1]}")
            elif len(parts) == 4 and parts[1] == "Low" and parts[2] == "Medium" and parts[3] == "High":
                if empty_count == 3:
                    new_headers.append(f"{main_part} {parts[1]}")
                    new_headers.append(f"{main_part} {parts[2]}")
                    new_headers.append(f"{main_part} {parts[3]}")
            elif "crosses" in parts[1] and "runs" in parts[0]:
                if empty_count == 2:
                    new_headers.append("Penalty area entries runs")
                    new_headers.append("Penalty area entries crosses")
            else:
                for k in range(1, len(parts)):
                    if k <= empty_count:
                        new_headers.append(f"{main_part} {parts[k]}")
            i += empty_count + 1
        else:
            new_headers.append(current_header)
            i += 1
    df.columns = new_headers
    df = df.iloc[1:].reset_index(drop=True)
    for col in df.columns:
        if col and not pd.isna(col):
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
    return df