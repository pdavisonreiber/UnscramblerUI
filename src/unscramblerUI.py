import argparse
import os
import tkinter as tk
from tkinter.filedialog import askopenfilename
from PyPDF2 import PdfFileReader, PdfFileWriter

def cropPageLeft(page):
	width = page.mediaBox.lowerRight[0]
	height = page.mediaBox.upperLeft[1]
	
	if width > height:
		page.cropBox.lowerLeft = (0, 0)
		page.cropBox.lowerRight = (width/2, 0)
		page.cropBox.upperLeft = (0, height)
		page.cropBox.upperRight = (width/2, height)
	else:
		page.cropBox.lowerLeft = (0, height/2)
		page.cropBox.lowerRight = (width, height/2)
		page.cropBox.upperLeft = (0, height)
		page.cropBox.upperRight = (width, height)
		

def cropPageRight(page):
	width = page.mediaBox.lowerRight[0]
	height = page.mediaBox.upperLeft[1]
	
	if width > height:
		page.cropBox.lowerLeft = (width/2, 0)
		page.cropBox.lowerRight = (width, 0)
		page.cropBox.upperLeft = (width/2, height)
		page.cropBox.upperRight = (width, height)
	else:
		page.cropBox.lowerLeft = (0, 0)
		page.cropBox.lowerRight = (width, 0)
		page.cropBox.upperLeft = (0, height/2)
		page.cropBox.upperRight = (width, height/2)
	
	
def splitPDF(document, pagesPerDocument):
	numberOfPages = document.getNumPages()
	
	if numberOfPages % pagesPerDocument != 0:
		raise Exception("Number of pages in file not divisible by " + str(pagesPerDocument) + ".")
		
	writers = [PdfFileWriter() for _ in range(numberOfPages // pagesPerDocument)]
	
	for i in range(numberOfPages):
		writers[i // pagesPerDocument].addPage(document.getPage(i))
		
	return writers
		
		
def splitA3Booklet(document1, document2, pagesPerDocument):
	numPages = document1.getNumPages()
	
	if numPages % pagesPerDocument != 0:
		raise Exception(f"Number of pages not divisible by {pagesPerDocument}.")
	
	#document2 = PdfFileWriter()
	#pages = [document1.getPage(i) for i in range(numPages)]
	#for page in pages:
	#	document2.addPage(page)
	
	page = document1.getPage(0)
	width = page.mediaBox.lowerRight[0]
	height = page.mediaBox.upperLeft[1]
	numDocs = numPages // pagesPerDocument
	
	pages1 = [document1.getPage(i) for i in range(numPages)]
	pages2 = [document2.getPage(i) for i in range(numPages)]
	
	arraysOfPages1 = [[document1.getPage(i) for i in range(k * pagesPerDocument, (k + 1) * pagesPerDocument)] for k in range(numDocs)]
	arraysOfPages2 = [[document2.getPage(i) for i in range(k * pagesPerDocument, (k + 1) * pagesPerDocument)] for k in range(numDocs)]
	
	#arraysOfPages1 = numpy.array_split(pages1, numDocs)
	#arraysOfPages2 = numpy.array_split(pages2, numDocs)
	
	outputWriter = PdfFileWriter()
	
	for i in range(numDocs):
		writer = PdfFileWriter()
		
		for j in range(pagesPerDocument):
			cropPageLeft(arraysOfPages1[i][j])
			cropPageRight(arraysOfPages2[i][j])
			
			if j % 2 == 0:
				writer.insertPage(arraysOfPages1[i][j])
				writer.addPage(arraysOfPages2[i][j])	
			if j % 2 == 1:
				writer.addPage(arraysOfPages1[i][j])
				writer.insertPage(arraysOfPages2[i][j])	
			
		for page in [writer.getPage(i) for i in range(writer.getNumPages())]:
			outputWriter.addPage(page)
			
	return outputWriter
	
	
def scramble(document, pagesPerDocument, split=False):
	numberOfPages = document.getNumPages()
	
	if numberOfPages % pagesPerDocument != 0:
		raise Exception("Number of pages in file not divisible by " + str(pagesPerDocument) + ".")
	
	writers = splitPDF(document, pagesPerDocument)
	outputWriters = [PdfFileWriter() for _ in range(pagesPerDocument)]
	
	for writer in writers:
		for i in range(writer.getNumPages()):
			outputWriters[i].addPage(writer.getPage(i))
			
	if split:
		return outputWriters
	else:
		finalWriter = PdfFileWriter()
	
		for outputWriter in outputWriters:
			for page in [outputWriter.getPage(i) for i in range(outputWriter.getNumPages())]:
				finalWriter.addPage(page)
	
		return finalWriter
	
def saveDocuments(documents, filenamePrefix):
	os.mkdir(filenamePrefix + "_output")
	directory = "./" + filenamePrefix + "_output"

	for i, document in enumerate(documents):
		filename = filenamePrefix + f"_{i + 1}.pdf"
		filePath = os.path.join(directory, filename)
		
		with open(filePath, "wb") as output:
			document.write(output)
	
	
		
def unscrambler(filename, pagesPerDocument, isBooklet, split, rearrange):
	pdf = open(filename, "rb")
	document = PdfFileReader(pdf)
	document2 = PdfFileReader(pdf)
	
	filenamePrefix = filename.replace(".pdf", "")
	
	if rearrange:
		if isBooklet:
			document = splitA3Booklet(document, document2, pagesPerDocument)
			pagesPerDocument *= 2
		
		if split:
			documents = scramble(document, pagesPerDocument, True)
			saveDocuments(documents, filenamePrefix)
		else:
			document = scramble(document, pagesPerDocument)
			with open(f"{filenamePrefix}_output.pdf", "wb") as output:
				document.write(output)
			
	elif isBooklet:
		document = splitA3Booklet(document, document2, pagesPerDocument)
		pagesPerDocument *= 2
		
		if split:
			documents = splitPDF(document, pagesPerDocument)
			saveDocuments(documents, filenamePrefix)
		else:
			with open(f"{filenamePrefix}_output.pdf", "wb") as output:
				document.write(output)
				
	elif split:
		documents = splitPDF(document, pagesPerDocument)
		saveDocuments(documents, filenamePrefix)
	else:
		print("You must select at least one option: -r, -s, or -b.")
	
		
def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("filename")
	parser.add_argument("numpages", type=int, help="The number of pages per document")
	parser.add_argument("-b", "--booklet", action="store_true", help="Use this option if the original is an A3 booklet. Source PDF is expected to be in landscape with the middle pages coming first.")
	parser.add_argument("-s", "--split", action="store_true", help="Use this option if you would like the output to be split into multiple files.")
	parser.add_argument("-r", "--rearrange", action="store_true", help="Use this option to rearrange the pages.")

	args = parser.parse_args()
	
	unscrambler(args.filename, args.numpages, args.booklet, args.split, args.rearrange)

def browseFiles():
    global filename
    global button_unscramble
    filename.set(askopenfilename(filetypes =[('PDFs', '*.pdf')]))
    
    

window = tk.Tk()
window.title("Unscrambler")
window.geometry("500x500")

file_explorer_frame = tk.Frame(window)
file_explorer_frame.pack(side = tk.TOP, fill = "x", padx = 20)
label_file_explorer = tk.Label(file_explorer_frame, text = "Please select a file")
label_file_explorer.pack(side = tk.LEFT)
button_explore = tk.Button(file_explorer_frame, text = "Browse Files", command = browseFiles)
button_explore.pack(side = tk.RIGHT)

filename = tk.StringVar(value="none")
selected_file_frame = tk.Frame(window)
selected_file_frame.pack(side = tk.TOP, fill = "x", padx = 20)
label_selected_file = tk.Label(selected_file_frame, text = "Selected file")
label_selected_file.pack(side = tk.LEFT)
selected_file_name = tk.Label(selected_file_frame, textvariable=filename)
selected_file_name.pack(side = tk.RIGHT)


def increment_split_var():
    global number_of_pages
    number_of_pages.set(number_of_pages.get() + 1)

def decrement_split_var():
    global number_of_pages
    if number_of_pages.get() > 1:
        number_of_pages.set(number_of_pages.get() - 1)

number_of_pages = tk.IntVar(value=1)
page_number_frame = tk.Frame(window)
page_number_frame.pack(side = tk.TOP, fill = "x", padx = 20)
label_page_number = tk.Label(page_number_frame, text = "Pages per document")
label_page_number.pack(side = tk.LEFT)
plus_button = tk.Button(page_number_frame, text = "+", command=increment_split_var)
plus_button.pack(side = tk.RIGHT)
label_number_of_pages = tk.Label(page_number_frame, textvariable = number_of_pages)
label_number_of_pages.pack(side = tk.RIGHT)
minus_button = tk.Button(page_number_frame, text = "–", command=decrement_split_var)
minus_button.pack(side = tk.RIGHT)


paper_size_var = tk.StringVar(value="A4")
option1_frame = tk.Frame(window)
option1_frame.pack(side = tk.TOP, fill="x", padx = 20)
option1_label = tk.Label(option1_frame, text = "Original paper size")
option1_label.pack(side = tk.LEFT)
option1_radio_button2 = tk.Radiobutton(option1_frame, text="A3", var=paper_size_var, value="A3")
option1_radio_button2.pack(side = tk.RIGHT)
option1_radio_button1 = tk.Radiobutton(option1_frame, text="A4", var=paper_size_var, value="A4")
option1_radio_button1.pack(side = tk.RIGHT)

rearrange_var = tk.IntVar(value = 0)
option2_frame = tk.Frame(window)
option2_frame.pack(side = tk.TOP, fill="x", padx = 20)
option2_label = tk.Label(option2_frame, text = "Rearrange pages")
option2_label.pack(side = tk.LEFT)
option2_checkbutton = tk.Checkbutton(option2_frame, var=rearrange_var, offvalue=0, onvalue=1)
option2_checkbutton.pack(side = tk.RIGHT)

def unscramble():
    global filename
    global number_of_pages
    global paper_size_var
    global split_var
    global rearrange_var
    
    unscrambler(filename.get(), number_of_pages.get(), paper_size_var.get() == "A3", split_var.get() == 1, rearrange_var.get() == 1)

split_var = tk.IntVar(value = 0)
option3_frame = tk.Frame(window)
option3_frame.pack(side = tk.TOP, fill="x", padx = 20)
option3_label = tk.Label(option3_frame, text = "Split document")
option3_label.pack(side = tk.LEFT)
option3_checkbutton = tk.Checkbutton(option3_frame, var=split_var, offvalue=0, onvalue=1)
option3_checkbutton.pack(side = tk.RIGHT)

go_button_frame = tk.Frame(window)
go_button_frame.pack(side = tk.TOP, fill="x", padx = 20)
button_unscramble = tk.Button(go_button_frame, text = "Unscramble!", command=unscramble)
button_unscramble.pack()

window.mainloop()
