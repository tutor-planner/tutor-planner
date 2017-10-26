\documentclass[a4paper,smallheadings, 12pt]{scrartcl}
\renewcommand{\familydefault}{\sfdefault}
\usepackage[a4paper, total={18cm, 26cm}]{geometry}



\usepackage[utf8]{inputenc}

\usepackage[T1]{fontenc}

\usepackage[english,ngerman]{babel}

\usepackage{marginnote}

\usepackage{amsmath, amssymb, amsfonts}

\usepackage[table]{xcolor}

\usepackage{url, listings}
\lstset{breaklines,commentstyle=\small\ttfamily,basicstyle=\scriptsize\ttfamily}

\pagestyle{empty}
\begin{document}
\begin{center}
\textbf{\huge Kontaktdaten}
\end{center}
\section*{\LARGE Tutoren}
\newcommand{\hdr}[1]{\textbf{\large #1}}
\begin{table}[h!]
    \rowcolors{2}{gray!25}{white}
    \begin{tabular}{llll}
\hdr{Name} & \hdr{Vorname} & \hdr{E-Mail} & \hdr{Telephone}\\\hline
% for tutor in tutors.values():
${tutor.last_name} & ${tutor.first_name} & ${tutor.email} & ${tutor.phone}\\
% endfor
    \end{tabular}
\end{table}
\section*{\LARGE WiMis}
\begin{table}[h!]
    \rowcolors{2}{gray!25}{white}
    \begin{tabular}{llll}
\hdr{Name} & \hdr{Vorname} & \hdr{E-Mail} & \hdr{Telephone}\\\hline
% for wm in wms:
${wm['last_name']} & ${wm['first_name']} & ${wm['email']} & ${wm['phone']}\\
% endfor
    \end{tabular}
\end{table}
\end{document}
