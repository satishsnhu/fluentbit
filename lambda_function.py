import boto3, os, csv, io, json, time
from botocore.session import Session

# === Configuration ===
BATCH_SIZE = 20          # Number of rows to process per Bedrock call
PROFILE = "pii_mask"     # Named AWS CLI profile
REGION = "us-east-1"     # Bedrock region

# === AWS Clients ===
session = Session(profile=PROFILE)
bedrock = session.client("bedrock-runtime", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)


# === Helper: Call Claude for redaction ===
def redact_with_claude(csv_chunk: str) -> str:
    """
    Sends a chunk of CSV data to Bedrock Claude Sonnet 5 to redact PII.
    """
    prompt = f"""
You are a data redactor. Remove or mask all PII (emails, SSNs, phone numbers, addresses, credit cards)
from the following CSV data, but KEEP the CSV structure and headers intact.

Input CSV:
{csv_chunk}
Return only the sanitized CSV data, without any commentary.
"""

    response = bedrock.converse(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"temperature": 0.0, "maxTokens": 4096}
    )

    return response["output"]["message"]["content"][0]["text"]


# === Helper: Batch Processing ===
def process_batch(batch_rows):
    csv_chunk = "\n".join([",".join(r) for r in batch_rows])
    redacted_csv = redact_with_claude(csv_chunk)

    reader = csv.reader(io.StringIO(redacted_csv))
    return list(reader)


# === Lambda Entry Point ===
def lambda_handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Ignore already processed or non-CSV files
        if not key.endswith(".csv") or key.startswith("masked/"):
            continue

        print(f"🔹 Processing file: s3://{bucket}/{key}")

        # Download file from S3
        obj = s3.get_object(Bucket=bucket, Key=key)
        csv_text = obj["Body"].read().decode("utf-8")

        reader = csv.reader(io.StringIO(csv_text))
        output = io.StringIO()
        writer = csv.writer(output)

        header = next(reader, None)
        if header:
            writer.writerow(header)

        batch = []
        row_count = 0

        for row in reader:
            batch.append(row)
            row_count += 1

            if len(batch) >= BATCH_SIZE:
                print(f"🔸 Redacting rows {row_count - BATCH_SIZE + 1}–{row_count}")
                redacted_rows = process_batch(batch)
                writer.writerows(redacted_rows)
                batch = []
                time.sleep(0.5)  # avoid throttling

        # process any remaining rows
        if batch:
            print(f"🔸 Redacting last {len(batch)} rows")
            redacted_rows = process_batch(batch)
            writer.writerows(redacted_rows)

        # Upload masked version
        masked_key = key.replace("incoming/", "masked/")
        s3.put_object(Bucket=bucket, Key=masked_key, Body=output.getvalue().encode("utf-8"))

        print(f"✅ Redacted CSV uploaded to: s3://{bucket}/{masked_key}")

    return {"status": "success"}
