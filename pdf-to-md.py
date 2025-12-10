import aspose.words as aw

doc = aw.Document("tamarin-manual.pdf")
doc.save("tamarin-manual.md", aw.SaveFormat.MARKDOWN)