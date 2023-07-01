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
    
    # add argument for output-file name
    parser.add_argument("--t_strategy", type = int)
    parser.add_argument("--t_sample_size", type = int)

    args = parser.parse_args()

    cmd = args.cmd
    timeout = args.timeout
    threads = args.threads
    strategy = args.t_strategy
    sample_size = args.t_sample_size

    print("Task:", cmd)
    print("Timeout:", f'{timeout}s' if timeout else "-")
    print("Threads:", f"{threads}")

    futures = []
    with ProcessPool(max_workers = threads, max_tasks = 1) as pool:

        cmd_final = cmd

        for arg in args.args:

            if re.search(r"%%%", cmd):
                cmd_final = re.sub(r"%%%", arg, cmd)
                
                # outputfile path
                output_file = "../stats/" + arg + "-baital_strategy" + str(strategy) + "-" + str(sample_size) + ".stats"
            else:
                cmd_final = f'{cmd} {arg}'

            print("Scheduling:", cmd_final)
            future = pool.submit(execute, timeout, cmd_final)
            
            # add outputfile path to futures list
            futures.append((future, cmd_final, output_file))

        pool.close()
        pool.join()

    for future, cmd, output_file in futures:
        print()
        try:
            time, out, err = future.result()

            print(f"\"{cmd}\" finished within {round(time.total_seconds(), 3)}s (t/o: {timeout}s)")

            if out:
                if output_file:
                    with open(output_file, "w+") as file:
                    	# write "error" to outputfile if execution failed, else console output
                        if err:
                            file.write("error")
                        else:
                            file.write(out)
                            file.write("\n")
                        file.close()
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
            if output_file:
                with open(output_file, "w+") as file:
                	# write "timeout" to outputfile if timeout
                        file.write("timeout")
                        file.close()


if __name__ == '__main__':
    main()
