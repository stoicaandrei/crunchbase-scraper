import subprocess
import threading
import re


def getClipboardData():
    p = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
    retcode = p.wait()
    data = p.stdout.read()
    return data.decode('utf-8')


clip = getClipboardData()


def check_for_clipboard_change():
    global clip

    threading.Timer(0.5, check_for_clipboard_change).start()

    clip2 = getClipboardData()

    if clip != clip2:
        clip = clip2
        print('clipboard changed')

        match = re.findall(r'\d+\.\n(?:.*\n){3}(.*)', clip)
        out = '\n'.join(match)

        with open('../data/list_of_company_names_raw.csv', 'a') as file:
            file.write('\n' + out)


check_for_clipboard_change()
