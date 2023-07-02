#!/usr/bin/env python3

from pebble import ProcessPool

import os
from os import path, linesep

import subprocess

import re

import argparse

from concurrent.futures import TimeoutError

from datetime import datetime as dt


def execute(call):

    time = dt.now()
    output = subprocess.run(call, capture_output = True, env = os.environ)

    return dt.now() - time, output.stdout.decode("utf-8"), output.stderr.decode("utf-8")


def timestamp():
    return dt.now().strftime("%Y-%m-%d-%H-%M-%S")


def main():

    parser = argparse.ArgumentParser(
        prog = "./timeouter.py",
        description = "small tool to execute commands in parallel with timeouts"
    )

    parser.add_argument("cmd", nargs = "+")
    parser.add_argument("--args", nargs = "*")
    parser.add_argument("--threads", type = int, default = 1)
    parser.add_argument("--timeout", type = int)    
    parser.add_argument("--log", action='store_true', default = False)    

    args = parser.parse_args()

    cmd = args.cmd


    timeout = args.timeout
    threads = args.threads

    logfile_out = path.join(os.getcwd(), f"pato-{timestamp()}-out.log")
    logfile_err = path.join(os.getcwd(), f"pato-{timestamp()}-err.log")
    statfile = path.join(os.getcwd(), f"pato-{timestamp()}.stats")


    print("Task:", cmd)
    print("Args:", args.args)
    print("Timeout:", f'{timeout}s' if timeout else "-")
    print("Threads:", f"{threads}")

    futures = []
    with ProcessPool(max_workers = threads, max_tasks = 1) as pool:

        if args.args:            
            for arg in args.args:
                cmd_final = []

                substituted = False
                for part in cmd:
                    if re.search(r"%%%", part):
                        part = re.sub(r"%%%", arg, part)
                        substituted = True

                    cmd_final.append(part)

                if not substituted:
                    cmd_final.append(arg)

                print("Scheduling:", " ".join(cmd_final))
                future = pool.submit(execute, timeout, cmd_final)
                futures.append((future, cmd_final))
        else:
            print("Scheduling:", cmd_final)
            future = pool.submit(execute, timeout, cmd_final)
            futures.append((future, cmd_final))

        pool.close()
        pool.join()


    with open(logfile_out, "w+") as lfo, open(logfile_err, "w+") as lfe, open(statfile, "w+") as sf:
        
        sf.write(f"cmd;time;error{linesep}")

        for future, cmd in futures:
            print()
            try:
                cmd = f'\"{" ".join(cmd)}\"'
                time, out, err = future.result()

                lfo.write(f"{cmd}{linesep}")
                lfo.writelines(out)

                lfe.write(f"{cmd}{linesep}")
                lfe.writelines(err)

                sf.write(f"{cmd};{time.total_seconds():.2f};False{linesep}")

                print(f"{cmd} finished within {round(time.total_seconds(), 3)}s (t/o: {timeout}s)")

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
                print(f"{cmd} timeouted within {timeout}s")
                sf.write(f"{cmd};;False{linesep}")
            except Exception as e:
                lfe.write(f"{cmd}{linesep}")
                lfe.write(e)
                sf.write(f"{cmd};;True{linesep}")


if __name__ == '__main__':
    main()
