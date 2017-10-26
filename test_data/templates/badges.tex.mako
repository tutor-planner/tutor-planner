\documentclass{article}
\renewcommand{\familydefault}{\sfdefault}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[german]{babel}
\usepackage[nohead,nofoot,left=15mm, right=0mm, top=10mm, bottom=5mm]{geometry}
\usepackage{filecontents}

\setlength{\parindent}{0pt}
\pagestyle{empty}
\raggedright

\begin{document}
% for tutor in tutors.values():
	\fbox{\begin{minipage}[t][54mm]{87mm}
	\centering
	\vspace{15mm}
	\textbf{{\fontsize{1.0cm}{1em}\selectfont C-Kurs Tutor/in}}\\
	\vspace*{1em}
	\rule{0.1\textwidth}{0.1cm}\\
	\vspace*{1em}
	{\textbf{{\fontsize{1cm}{1em}\selectfont ${tutor.first_name}}}}
	\end{minipage}}
% endfor
% for wm in wms:
	\fbox{\begin{minipage}[t][54mm]{87mm}
	\centering
	\vspace{15mm}
	\textbf{{\fontsize{1.0cm}{1em}\selectfont C-Kurs WiMi}}\\
	\vspace*{1em}
	\rule{0.1\textwidth}{0.1cm}\\
	\vspace*{1em}
	{\textbf{{\fontsize{1cm}{1em}\selectfont ${wm['first_name']}}}}
	\end{minipage}}
% endfor
\end{document}
