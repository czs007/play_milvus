# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import argparse
import time
import os
import signal
import sys

from threading import Timer
import numpy as np
from pymilvus import (
    Collection, Partition,
    connections, utility
)

from common import *

sift_dir_path = "/czsdata/sift1b/"
sift_dir_path = "/test/milvus/raw_data/sift1b/"
deep_dir_path = "/czsdata/deep1b/"
deep_dir_path = "/test/milvus/raw_data/deep1b/"

EF_SEARCHS = [50, 64, 80, 100, 128, 168, 200, 256]
NPROBES = [4, 6, 8, 12, 16, 20, 24, 32, 40, 50, 64, 128]

TOPK = 50
NQ = 10000
QueryFName = "query.npy"
RUN_NUM = 2

Spinner = spinning_cursor()

def connect_server(host):
    connections.connect(host=host, port=19530)
    print(f"connected")

def search_collection(collection, dataset, indextype):
    query_fname = ""
    metric_type = ""
    if dataset == DATASET_DEEP:
        metric_type = "IP"
        query_fname = os.path.join(deep_dir_path, QueryFName)
    elif dataset == DATASET_SIFT:
        query_fname = os.path.join(sift_dir_path, QueryFName)
        metric_type = "L2"

    if metric_type == "" or query_fname == "":
        raise_exception("wrong dataset")

    search_params = {"metric_type": metric_type, "params": {}}
    param_key = ""
    plist = []
    if indextype == IndexTypeIVF_FLAT:
        param_key = "nprobe"
        plist = NPROBES 
    elif indextype == IndexTypeHNSW:
        param_key = "ef"
        plist = EF_SEARCHS

    if not plist:
        raise_exception("wrong dataset")

    queryData = np.load(query_fname)
    query_list = queryData.tolist()[:NQ]

    for s_p in plist:
        run_counter = 0
        run_time = 0
        while(run_counter < RUN_NUM):
            start = time.time()
            search_params["params"][param_key] = s_p
            result = collection.search(query_list, "vec", search_params, TOPK, guarantee_timestamp=1)
            search_time = time.time() - start
            run_time = run_time + search_time 
            run_counter = run_counter + 1 
        aver_time = run_time * 1.0 / RUN_NUM

        fmt_str = "%s: %s, aeverage_time, qps: "%(param_key, s_p)
        print(fmt_str)
        print(aver_time, NQ*1.0/aver_time)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler(None))
    parser = argparse.ArgumentParser(
        description="Insert Data to Milvus user-defined ranges of .npy files")
    parser.add_argument("--host", type=str, nargs=1,
                        help="host:xx.xx.xx.xx", required=True)

    parser.add_argument('--dataset', type=str, nargs=1,
                        help="dataset: sift | deep", required=True)

    parser.add_argument('--index', type=str, nargs=1, 
                        help="index: HNSW | IVF_FLAT", required=True)

    args = parser.parse_args()
    host = args.host[0]
    dataset = args.dataset[0]
    indextype = args.index[0]

    print("Host:", host)
    print("Dataset:", dataset)
    print("IndexType", indextype)

    connect_server(host)
    collection = prepare_collection(dataset)
    search_collection(collection, dataset, indextype)
