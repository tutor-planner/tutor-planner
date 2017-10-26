\documentclass[a4paper,smallheadings]{scrartcl}
\renewcommand{\familydefault}{\sfdefault}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[english,ngerman]{babel}
\usepackage{longtable}
\usepackage[
  top=10mm,
  bottom=10mm,
  marginparsep=7mm,
  marginparwidth=10mm,
]{geometry}

<%
def red(task):
    if task.startswith("Rechner"):
        return 'Rechner\"ubung'
    else:
        return task
%>
\pagestyle{empty}
\begin{document}
\begin{center}
\textbf{\Huge C-Kurs Einsatzplan}\\
\textbf{\huge Aktualisiert: ${datum}}
\end{center}
\begin{table}[h!]
    \centering
    \begin{longtable}{ll}
        \textbf{Name} & ${tutor_name}\\
        \textbf{Stundenanzahl} & ${tutor.monthly_work_hours}\\
    \end{longtable}
\end{table}
\vspace{1cm}

\begin{tabular}{llllll}
    \centering
    \textbf{Tag} & \textbf{Zeit} & \textbf{Raum} &
    \textbf{Job}\\\hline
% for s in sorted(schedule, key=lambda k: (k["day"], k["time"])):
    ${day_index_to_string(s["day"])} & ${s["time"]}--${s["time"]+1} & ${s["room"]} & ${red(s["task"])}\\
% endfor
\end{tabular}\\[0.5cm]
Bei Problemen kontaktiert bitte ${wm['first_name']} ${wm['last_name']} via E-Mail ${wm['email']} oder
Telefon ${wm['phone']}.
\end{document}
