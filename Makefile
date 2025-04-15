blind_75.pdf: blind_75.html
	pandoc blind_75.html -o blind_75.pdf --pdf-engine=weasyprint --toc

blind_75.html: question_links.txt export_all_questions.py
	python export_all_questions.py