import sys
import os


# If any UDF is defined, the path of the UDF will be set to this variable
# and the path will be deleted when the process exits
# UDF config path will be f"{g_udf_path}/udf_config.xml"
# UDF script path will be f"{g_udf_path}/{func_name}.py"
g_udf_path = ""

chdb_version = (0, 6, 0)
if sys.version_info[:2] >= (3, 7):
    # get the path of the current file
    current_path = os.path.dirname(os.path.abspath(__file__))
    # change the current working directory to the path of the current file
    # and import _chdb then change the working directory back
    cwd = os.getcwd()
    os.chdir(current_path)
    from . import _chdb  # noqa

    os.chdir(cwd)
    engine_version = str(_chdb.query("SELECT version();", "CSV").bytes())[3:-4]
else:
    raise NotImplementedError("Python 3.6 or lower version is not supported")

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = ".".join(map(str, chdb_version))
except:  # pragma: no cover
    __version__ = "unknown"


# return pyarrow table
def to_arrowTable(res):
    """convert res to arrow table"""
    # try import pyarrow and pandas, if failed, raise ImportError with suggestion
    try:
        import pyarrow as pa
        import pandas
    except ImportError as e:
        print(f"ImportError: {e}")
        print('Please install pyarrow and pandas via "pip install pyarrow pandas"')
        raise ImportError("Failed to import pyarrow or pandas") from None
    if len(res) == 0:
        return pa.Table.from_batches([], schema=pa.schema([]))
    return pa.RecordBatchFileReader(res.bytes()).read_all()


# return pandas dataframe
def to_df(r):
    """convert arrow table to Dataframe"""
    t = to_arrowTable(r)
    return t.to_pandas(use_threads=True)


# wrap _chdb functions
def query(sql, output_format="CSV", path="", udf_path=""):
    global g_udf_path
    if udf_path != "":
        g_udf_path = udf_path
    lower_output_format = output_format.lower()
    if lower_output_format == "dataframe":
        return to_df(_chdb.query(sql, "Arrow", path=path, udf_path=g_udf_path))
    elif lower_output_format == "arrowtable":
        return to_arrowTable(_chdb.query(sql, "Arrow", path=path, udf_path=g_udf_path))
    else:
        return _chdb.query(sql, output_format, path=path, udf_path=g_udf_path)
