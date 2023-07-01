#!/usr/bin/env python3

from pebble import ProcessPool
import sys
import subprocess

import re

import argparse

from concurrent.futures import TimeoutError

from datetime import datetime as dt

def execute(call):

    time = dt.now()
    output = subprocess.run(re.split(r"\s+", call), capture_output = True)

    return dt.now() - time, output.stdout.decode("utf-8"), output.stderr.decode("utf-8")


def main():

    parser = argparse.ArgumentParser(
        prog = "./timeouter.py",
        description = "Small tool to execute commands in parallel with timeouts"
    )

    parser.add_argument("cmd")
    parser.add_argument("args", nargs = "*")
    parser.add_argument("--threads", type = int, default = 1)
    parser.add_argument("--timeout", type = int)    

    args = parser.parse_args()

    cmd = args.cmd
    timeout = args.timeout
    threads = args.threads

    print("Task:", cmd)
    print("Timeout:", f'{timeout}s' if timeout else "-")
    print("Threads:", f"{threads}")

    futures = []
    with ProcessPool(max_workers = threads, max_tasks = 1) as pool:

        cmd_final = cmd

        for arg in args.args:

            if re.search(r"%%%", cmd):
                cmd_final = re.sub(r"%%%", arg, cmd)
            else:
                cmd_final = f'{cmd} {arg}'

            print("Scheduling:", cmd_final)
            future = pool.submit(execute, timeout, cmd_final)
            futures.append((future, cmd_final))

        pool.close()
        pool.join()

    for future, cmd in futures:
        print()
        try:
            time, out, err = future.result()

            print(f"\"{cmd}\" finished within {round(time.total_seconds(), 3)}s (t/o: {timeout}s)")

            if out:
                print("-- stdout start", "-" * 32)
                print(out, end = "")
                print("-- stdout end", "-" * 34)

            if out and err:
                print()

            if err:
                print("-- stderr start", "-" * 32)
                print(err, end = "")
                print("-- stderr end", "-" * 34)


        except TimeoutError:
            print(f"\"{cmd}\" timeouted within {timeout}s")



if __name__ == '__main__':
    main()