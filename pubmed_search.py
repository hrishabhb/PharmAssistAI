import os
from Bio import Entrez, Medline

def search_related_papers(query, max_results=3):
    try:
        Entrez.email = os.environ.get("ENTREZ_EMAIL")

        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()

        id_list = record["IdList"]
        if not id_list:
            return [
                "No directly related papers found. Try broadening your search query."
            ]

        handle = Entrez.efetch(db="pubmed",
                               id=id_list,
                               rettype="medline",
                               retmode="text")
        records = Medline.parse(handle)

        related_papers = []
        for record in records:
            title = record.get("TI", "")
            authors = ", ".join(record.get("AU", []))
            citation = f"{authors}. {title}. {record.get('SO', '')}"
            url = f"https://pubmed.ncbi.nlm.nih.gov/{record['PMID']}/"
            related_papers.append(f"[{citation}]({url})")

        if not related_papers:
            related_papers = [
                "No directly related papers found. Try broadening your search query."
            ]

        return related_papers
    except Exception as e:
        print(f"Error occurred while searching for related papers: {e}")
        return [
            "An error occurred while searching for related papers. Please try again later."
        ]
