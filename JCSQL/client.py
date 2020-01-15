import os
import sys
import time
from datetime import timedelta
import threading
import traceback
from collections import deque
import csv
try:
    import numpy as np
    import pyodbc
    import cx_Oracle as cx
except Exception as e:
    print(e)


PRINT_HEADER = []
PRINT_FOOTER = []
PRINT_LOAD = '(...)'


def print_all(output):
    print(*PRINT_HEADER, sep='\n', flush=True)
    pretty_print_result(output)
    print(*PRINT_FOOTER, sep='\n', flush=True)
    sys.stdout.flush()


def cvs_print_result(output):
    writer = csv.writer(sys.stdout, dialect='excel', delimiter=',', lineterminator='\n', quoting=csv.QUOTE_ALL, escapechar='\\')
    writer.writerows(output)
    sys.stdout.flush()


def pretty_print_result(output):
    def check_line_end(val):
        v = str(val).replace('\r', '')
        if '\n' in v:
            return max(map(len, v.split('\n')))
        else:
            return len(v)

    l_output = np.array(output)
    to_str_repl_len = np.vectorize(check_line_end)
    max_col_length = np.amax(to_str_repl_len(l_output), axis=0)

    def proc_line_end(val, index):
        blob_list = str(val).replace('\r', '').split('\n')
        sm = np.sum(max_col_length[:index]) + 3 * index + 2
        res = [(' ' * (sm - 2) + '. ' if i > 0 else '') + str(value).replace('None', 'NULL') + ' ' * (max_col_length[index] - len(value)) + (' .' if i != len(blob_list) - 1 else '') for i, value in enumerate(blob_list)]
        return '\n'.join(res)

    # print result
    print('+' + ''.join(['-' * x + '--+' for x in max_col_length]))
    for row_index, row in enumerate(l_output):
        print('|' + ''.join([' ' + ((str(value).replace('None', 'NULL').replace('\r', '') + ' ' * (max_col_length[index] - len(str(value).replace('\r', '')))) if '\n' not in str(value) else proc_line_end(value, index)) + ' |' for index, value in enumerate(row)]))
        if row_index == 0 or row_index == len(l_output) - 1:
            print('+' + ''.join(['-' * x + '--+' for x in max_col_length]))

    print('\nFetched {0} rows'.format(np.size(l_output, 0) - 1))


def connect_to_db(conn_str, env):
    db = None
    for _ in range(50):  # 50 attempts
        if env == 'oracle':
            db = cx.connect(conn_str, encoding='utf-8')
        else:
            db = pyodbc.connect(conn_str, autocommit=True, timeout=0)
        if db:
            break
    if not db:
        print('\nCant connect in 50 attempts. Exit 1\n', flush=True)
        os._exit(1)
    PRINT_HEADER.append('\n[{0}] Connected to {1}\n'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), env))
    return db


def fetch_data(cur, res, fetch_num, is_fetched_all_rows, with_header=False):
    if is_fetched_all_rows:
        return True

    if not cur.description:
        res += [['done.']]
        return True

    if with_header:
        headers = tuple([i[0].lower() for i in cur.description])
        res.append(headers)

    if fetch_num == -1:
        res += cur.fetchall()
        return True

    result = cur.fetchmany(fetch_num)
    res += result

    if len(result) == 0 or len(result) <= fetch_num - 1:
        return True

    return False


def read_input(msg_q):
    while True:
        msg_q.append(sys.stdin.readline())


def main():

    os.environ['PYTHONIOENCODING'] = 'utf-8'

    env = sys.argv[1]
    conn_str = sys.argv[2]
    query_file_name = sys.argv[3]
    # qtype = sys.argv[4]
    fetch_num = int(sys.argv[5])
    query = ''
    sys.path.append(os.path.dirname(query_file_name))

    try:
        with open(query_file_name, 'rb') as f:
            query = f.read().decode('utf-8').replace('\r\n', '\n')

        db = connect_to_db(conn_str, env)
        cur = db.cursor()
        output = []
        queries = list(filter(None, query.split(';\n')))
        len_q = len(queries)
        for i, query in enumerate(queries):
            is_fetched_all_rows = False
            PRINT_HEADER.append(query + '\n')
            start = time.time()
            cur.execute(query)

            if len_q > 1:
                output = []

            is_fetched_all_rows = fetch_data(cur, output, fetch_num, is_fetched_all_rows, with_header=True)

            end = time.time()
            PRINT_FOOTER.append('\nElapsed {0} s\n'.format(str(timedelta(seconds=end - start))))

            print_all(output)

            if i < len_q - 1:
                PRINT_HEADER.pop()
                PRINT_FOOTER.pop()

        if not is_fetched_all_rows:
            print(PRINT_LOAD, flush=True)
            PRINT_FOOTER.append(PRINT_LOAD)
        else:
            print('Fetched all rows.', flush=True)

        # default timeout 30 sec
        timeout = time.time() + 30
        input_msgs = deque()

        input_t = threading.Thread(target=read_input, args=(input_msgs,))
        input_t.daemon = True
        input_t.start()
        while time.time() < timeout:
            if len(input_msgs) == 0:
                time.sleep(0.2)
                continue

            cmd = input_msgs.popleft().split('==')
            if cmd[0] == 'load':
                if not is_fetched_all_rows:
                    is_fetched_all_rows = fetch_data(cur, output, int(cmd[1]), is_fetched_all_rows)
                    if is_fetched_all_rows:
                        PRINT_FOOTER[-1] = 'Fetched all rows.'
                print_all(output)
                timeout += 10
            elif cmd[0] == 'csv':
                if not is_fetched_all_rows:
                    is_fetched_all_rows = fetch_data(cur, output, int(cmd[1]), is_fetched_all_rows)
                cvs_print_result(output)
                # break
            else:
                break

    except cx.Error as oracle_dbe:
        e_msg = '\n{0}\n'.format(oracle_dbe)
        print(*PRINT_HEADER, sep='\n', flush=True)
        print(e_msg)
    except pyodbc.Error as pyodbc_error:
        e_msg = '\n{0}\n'.format(pyodbc_error.args[1])
        print(*PRINT_HEADER, sep='\n', flush=True)
        print(e_msg)
    except Exception:
        print(traceback.format_exc())
    finally:
        cur.close()
        db.close()
        sys.stdout.flush()
        os._exit(1)

    sys.stdout.flush()
    cur.close()
    db.close()
    os._exit(0)


if __name__ == '__main__':
    main()
