# Oracle/IMPALA/HIVE utilities functions

import os
import csv
import traceback
from datetime import datetime
from decimal import Decimal
try:
    import wx
    import wx.dataview
except Exception:
    pass

RAND_MAX = 999999999999999

SQLPLUS_DEFAULT_PARAMS = '''
ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS';
SET SERVEROUTPUT ON;
SET TAB OFF;
SET PAGESIZE 0;
SET SQLBLANKLINES ON;
SET TIMING ON;
SET ECHO ON;
'''


def get_text(view):
    selected_text = ''
    if view.sel():
        for region in view.sel():
            if region.empty():
                selected_text += view.substr(view.line(region))
                view.sel().add(view.line(region))
            else:
                selected_text += view.substr(region)

    if not selected_text:
        return ''

    text = selected_text.strip('; \t\n\r')
    return text


def prepare_oracle(query, qtype, is_query_dml):
    if qtype == 'query':
        if is_query_dml:
            tool = 'python'
        else:
            tool = 'sqlplus'
            if query.endswith('/'):
                query = '{0}{1}\n{2}'.format(SQLPLUS_DEFAULT_PARAMS, query, 'exit')
            else:
                query = '{0}{1};\n{2}'.format(SQLPLUS_DEFAULT_PARAMS, query, 'exit')
    elif qtype == 'explain':
        tool = 'sqlplus'
        LINE_SIZE_PARAM = '''SET LINESIZE 1000;'''
        query = "{0}{1}EXPLAIN PLAN FOR\n{2};\nSELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);".format(LINE_SIZE_PARAM, SQLPLUS_DEFAULT_PARAMS, query)

    return tool, query, None


def prepare_impala(query, qtype, is_query_dml):
    tool = 'python'
    if qtype == 'explain':
        query = 'EXPLAIN\n {0}'.format(query)
        fetch = -1
    else:
        fetch = -1 if not is_query_dml else None

    return tool, query, fetch

def prepare_snowflake(query, qtype, is_query_dml):
    tool = 'python'
    if qtype == 'explain':
        query = 'EXPLAIN\n {0}'.format(query)
        fetch = -1
    else:
        fetch = -1 if not is_query_dml else None

    return tool, query, fetch


def prepare_hive(query, qtype, is_query_dml):
    tool = 'java'
    if qtype == 'explain':
        query = 'EXPLAIN\n {0}'.format(query)
        fetch = -1
    else:
        fetch = -1 if not is_query_dml else None

    return tool, query, fetch


def prepare_query_file(view, env, qtype):
    sel_text = get_text(view)
    if not sel_text:
        print('nothing selected')
        return

    is_query_dml = any(map(sel_text[:6].lower().startswith, ['select', 'with']))

    if env == 'oracle':
        tool, cl_query, fetch = prepare_oracle(sel_text, qtype, is_query_dml)
    elif env == 'impala':
        tool, cl_query, fetch = prepare_impala(sel_text, qtype, is_query_dml)
    elif env == 'hive':
        tool, cl_query, fetch = prepare_hive(sel_text, qtype, is_query_dml)
    elif env == 'snowflake':
        tool, cl_query, fetch = prepare_snowflake(sel_text, qtype, is_query_dml)
    else:
        return

    tmp_file_name = 'tmp_{tool}_dt_{dt}.sql'.format(tool=tool, dt=datetime.now().strftime("%Y_%m_%d_%H_%M_%S.%f"))
    tmp_file_path = os.path.join(os.path.dirname(__file__), 'tmp', tmp_file_name)

    try:
        with open(tmp_file_path, 'wb+') as tf:
            tf.write(cl_query.encode('utf-8'))
    except Exception:
        traceback.print_exc()

    return tool, tmp_file_path, fetch


def result_to_csv(file_path, headers, dataset):
    file_path = file_path + '.csv' if not file_path.endswith('.csv') else file_path
    output_file = open(file_path, 'w', newline='', encoding='utf-8')
    writer = csv.writer(output_file, dialect='excel', delimiter=',', lineterminator='\n', quoting=csv.QUOTE_ALL, escapechar='\\')
    try:
        writer.writerow(headers)
        writer.writerows(dataset)
    except Exception as e:
        print(e)
    output_file.close()


def show_result_in_gui(res_cur):
    headers = tuple([i[0].lower() for i in res_cur.description])

    def ask_file_path():
        with wx.FileDialog(frame, "Save csv file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return ''
            return fileDialog.GetPath()

    def save_to_csv(event):
        file_path = ask_file_path()
        if file_path:
            update_table(-1)
            result_to_csv(file_path, headers, data_store)
            dialog = wx.MessageDialog(frame, 'Done.')
            dialog.ShowModal()
        event.Skip()

    def on_char_event(event):
        if event.GetKeyCode() == wx.WXK_END:
            update_table(-1)
        event.Skip()

    def show_popup_menu(event):
        popupID1 = wx.NewId()
        menu = wx.Menu()
        item = wx.MenuItem(menu, popupID1, "Save to csv")
        menu.Append(item)
        menu.Bind(wx.EVT_MENU, save_to_csv, id=popupID1)
        wx.Window.PopupMenu(frame, menu)
        menu.Destroy()
        event.Skip()

    def scroll_event_handler(event):
        r = data_view.GetScrollRange(wx.VERTICAL)
        s = data_view.GetScrollThumb(wx.VERTICAL)
        pos = data_view.GetScrollPos(wx.VERTICAL)
        if r - s == pos:
            update_table()
        event.Skip()

    def update_table(fetch_num=50):
        if fetch_num == -1:
            result = res_cur.fetchall()
        else:
            result = res_cur.fetchmany(fetch_num)

        for row in result:
            row = tuple([str(r).replace('None', 'NULL') if type(r) == datetime or type(r) == Decimal or r is None else r for r in row])
            data_view.AppendItem(row)
            data_store.append(row)

    app = wx.App(False)
    width, height = wx.GetDisplaySize()
    frame = wx.Frame(None, wx.ID_ANY, "result", size=wx.Size(width * 0.8, height * 0.50), pos=(width * 0.10, height * 0.4))

    data_view = wx.dataview.DataViewListCtrl(frame, wx.ID_ANY, style=wx.dataview.DV_MULTIPLE | wx.dataview.DV_ROW_LINES)
    data_store = []

    for header_name in headers:
        data_view.AppendTextColumn(header_name, width=wx.COL_WIDTH_AUTOSIZE, flags=wx.dataview.DATAVIEW_COL_SORTABLE | wx.dataview.DATAVIEW_COL_RESIZABLE | wx.dataview.DATAVIEW_COL_REORDERABLE)

    data_view.Bind(wx.EVT_SCROLLWIN, scroll_event_handler)
    data_view.Bind(wx.dataview.EVT_DATAVIEW_COLUMN_HEADER_RIGHT_CLICK, show_popup_menu)
    data_view.Bind(wx.EVT_CHAR, on_char_event)

    update_table()

    frame.Show(True)
    app.MainLoop()
