\documentclass[a4paper,smallheadings, fontsize=${fontsize}]{scrartcl}
\usepackage[a4paper, left=1.5cm, right=1.5cm, top=${top}cm, bottom=${bottom}cm]{geometry}

\renewcommand{\familydefault}{\sfdefault}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[english,ngerman]{babel}
\usepackage{amsmath, amssymb, amsfonts}
\usepackage{lscape, tikz, graphicx}
\usepackage{booktabs}
\usetikzlibrary{backgrounds}

\newcommand{\Tuto}{T}
\newcommand{\Rech}{R\"U}
\newcommand{\Lect}{VL}
\newcommand{\None}{-}
\pagestyle{empty}
\renewcommand{\arraystretch}{1.3}

<%
def slot(room, time, room_bookings, supervised_rooms, activity_string):
	if room in supervised_rooms[time]:
		return activity_string
	elif room in room_bookings[time]:
		return "\ensuremath{\diamond}"
	else:
		return "-"

def createC(times):
    return "".join(["c"] * times)
%>

\begin{document}
\begin{table}[h!]
    \centering
    \begin{tabular}{l}
        \toprule
        \textbf{\Huge{${dayString}}} \\
        \bottomrule
    \end{tabular}
\end{table}
\begin{table}[h!]
    \centering
    \begin{tabular}{l${createC(numberOfHours)}}

\hline
\textbf{Seminarräume}
% for time in range(dayBegin, dayEnd):
    & \textbf{${time}:00}
% endfor
        \\\hline

% for name in sorted(seminar_room_names):
    ${name}
    %for time in range(dayBegin, dayEnd):
        & ${slot(name, time,  room_bookings,  supervised_rooms, "T")}
    %endfor
    \\
% endfor
% if not seminar_room_names:
    \multicolumn{${numberOfHours+1}}{c}{Heute findet kein Tutorium statt.} \\
% endif
\hline \\[-4pt]
\hline
\textbf{Rechnerräume}
% for time in range(dayBegin, dayEnd):
    & \textbf{${time}:00}
% endfor
        \\\hline

% for name in sorted(pool_room_names):
    ${name}
    %for time in range(dayBegin, dayEnd):
        & ${slot(name, time,  room_bookings,  supervised_rooms, "R")}
    %endfor
	\\
% endfor
% if not pool_room_names:
    \multicolumn{${numberOfHours+1}}{c}{Heute findet keine Rechnerübung statt.} \\
% endif
    \bottomrule \\[-12pt]
    \multicolumn{${numberOfHours+1}}{c}{T: Tutorium\quad R: Rechner\"ubung \quad \ensuremath{\diamond}: Raum kann frei benutzt werden.} \\[2pt]
    \bottomrule
    \end{tabular}
\end{table}
\vspace{-12pt}
\begin{center}

Die Vorlesung ist in der Übersicht nicht enthalten.

ISIS: www.isis.tu-berlin.de/ $\rightarrow$ `Einführung in die Programmierung'

Helpdesk: TEL 109 (${dayBegin}:00 - ${dayEnd-1}:30)

\end{center}
\end{document}
