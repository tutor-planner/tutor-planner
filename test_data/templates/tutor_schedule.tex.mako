\documentclass[landscape, a4paper,smallheadings,fontsize=${fontsize}pt]{scrartcl}
\usepackage[a4paper, left=1.5cm, right=1.5cm, top=${top}cm, bottom=${bottom}cm, marginparsep=7mm, marginparwidth=10mm]{geometry}
\renewcommand{\familydefault}{\sfdefault}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[english,ngerman]{babel}
\usepackage{amsmath, amssymb, amsfonts}
\usepackage{lscape, tikz, graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usetikzlibrary{backgrounds}
\usepackage{pbox}


\newcommand{\Tuto}{T}
\newcommand{\Rech}{R\"U}
\newcommand{\Lect}{VL}
\newcommand{\None}{-}
\pagestyle{empty}
\renewcommand{\arraystretch}{1.2}

<%

def slot(time, tutorsAtTime, bookedRooms, roomName):
    print(">>>")
    print(tutorsAtTime)
    print(roomName)
    if roomName in tutorsAtTime:
        print("fine!")
        stringIt = ", ".join(tutorsAtTime[roomName])
        print(stringIt)
        return stringIt
    elif roomName in bookedRooms[time]:
        return "\ensuremath{\diamond}"
    else:
        return "-"

def createC(times):
    return "".join(["p{2.75cm}"] * times)
%>

\begin{document}
{\huge{\textbf{C-Kurs Einsatzplanübersicht ${dayString}}} }\\
\begin{table}[htp]
    \centering
    \begin{longtable}{l${createC(numberOfHours)}}
        \textbf{\Large R\"aume} & \multicolumn{${numberOfHours}}{c}{\Large
    \textbf{Zeiten}}\\[0.5em]
% for time in range(dayBegin, dayEnd):
    & ${time}:00
% endfor
       \\\hline
% for name in sorted(rooms.keys()):
${name}
    % for time in range(dayBegin, dayEnd):
        &  ${slot(time,  tutorials[time],  bookedRooms, name)}
    % endfor
    \\\hline
% endfor
    \bottomrule
    \end{longtable}
\end{table}
\end{document}
