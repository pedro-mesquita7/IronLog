import time

import boto3

from shared.constants import ATHENA_DATABASE, ATHENA_OUTPUT_BUCKET, ATHENA_WORKGROUP

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("athena")
    return _client


def reset_client():
    """Reset cached Athena client. Used in tests."""
    global _client
    _client = None


class AthenaQueryError(Exception):
    pass


def run_athena_query(sql):
    """Execute an Athena SQL query and return results as a list of dicts.

    Polls until the query completes. Raises AthenaQueryError on failure.
    """
    client = _get_client()

    # Workgroup has EnforceWorkGroupConfiguration=true and configures
    # output location, so we omit ResultConfiguration here.
    resp = client.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": ATHENA_DATABASE},
        WorkGroup=ATHENA_WORKGROUP,
    )
    query_id = resp["QueryExecutionId"]

    # Poll for completion (0.5s intervals, up to ~25s)
    for _ in range(50):
        status = client.get_query_execution(QueryExecutionId=query_id)
        state = status["QueryExecution"]["Status"]["State"]

        if state == "SUCCEEDED":
            break
        if state in ("FAILED", "CANCELLED"):
            reason = status["QueryExecution"]["Status"].get(
                "StateChangeReason", "Unknown error"
            )
            raise AthenaQueryError(f"Query {state}: {reason}")

        time.sleep(0.5)
    else:
        raise AthenaQueryError("Query timed out")

    # Fetch results with pagination
    rows = []
    columns = None
    kwargs = {"QueryExecutionId": query_id, "MaxResults": 1000}

    while True:
        result = client.get_query_results(**kwargs)
        result_rows = result["ResultSet"]["Rows"]

        if columns is None:
            # First page: first row is column headers
            columns = [col["VarCharValue"] for col in result_rows[0]["Data"]]
            data_rows = result_rows[1:]
        else:
            data_rows = result_rows

        for row in data_rows:
            record = {}
            for i, cell in enumerate(row["Data"]):
                val = cell.get("VarCharValue")
                record[columns[i]] = val
            rows.append(record)

        next_token = result.get("NextToken")
        if not next_token:
            break
        kwargs["NextToken"] = next_token

    return rows
