import pandas as pd
import re

df = pd.read_csv("http.csv")

port_pattern = re.compile(r'(\d+)\s*>\s*(\d+)')

http_keywords = ["GET", "POST", "HEAD", "PUT", "DELETE", "HTTP/1.1"]

with open("output.txt", "w") as f:
    header = (
        f"{'Source IP':<20}"
        f"{'Destination IP':<20}"
        f"{'Source Port':<15}"
        f"{'Destination Port':<20}"
        f"{'HTTP Request / Response':<40}\n"
    )

    f.write(header)
    f.write("=" * 115 + "\n")

    for _, row in df.iterrows():
        src_ip = str(row['Source'])
        dst_ip = str(row['Destination'])

        src_port = "-"
        dst_port = "-"
        http_info = "-"
        match = port_pattern.search(str(row['Info']))

        if match:
            src_port, dst_port = match.groups()

        info = str(row['Info'])
        protocol = str(row['Protocol'])
        if protocol == "HTTP" or any(k in info for k in http_keywords):
            http_info = info

        f.write(
            f"{src_ip:<20}"
            f"{dst_ip:<20}"
            f"{src_port:<15}"
            f"{dst_port:<20}"
            f"{http_info:<40}\n"
        )

print("output saved to output.txt")
