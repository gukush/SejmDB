import requests
import io
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
import pyodbc

some_pass = "MY_PASSWORD"
some_uid = "MY_USERNAME"
some_server = "MY_SERVER"
cnxn = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};"+f"Server={some_server};Database=SejmVote;UID={some_uid};PWD={some_pass}")
cursor = cnxn.cursor()
createString = "IF NOT EXISTS (SELECT * FROM sys.tables WHERE NAME='PARTIES') CREATE TABLE PARTIES(NAME varchar(40), PARTY48 varchar(40), PARTY1 varchar(40), PRIMARY KEY (NAME) )"
cursor.execute(createString)
cnxn.commit()
def namePartyParser(myString):
    nameList=[]
    partyList=[]
    newString=""
    x=myString.split('\n')
    count=0
    it=15
    while it < len(x):
        temp = x[it].strip()
        if(temp !=''):
            if '(' in temp and ')' in temp:
                arr=temp.replace(')','(')
                arr =arr.split('(')
                partyName=arr[0].strip()
                partyCount=int(arr[1])
                print(f"{partyName} has {partyCount} members")
                partyList.append((partyName,partyCount))
            elif any(c.isdigit() for c in temp):#or("(" in temp or ")" in temp)or(len(x)<4)or(len(x)>40):#or("Sejm" in temp)or("Pkt" in temp)or("Posiedzenie" in temp):
                #print(f"{temp} passed this value ")
                pass
            elif len(temp)>3:#and len(temp)<=40:         
                temp = temp.replace('pr.','#')
                temp = temp.replace('za','#')
                temp = temp.replace('ws.','#')
                temp = temp.replace('ng.','#')
                firstBreak = temp.split('#')
                if not any(c.islower() for c in temp):
                    #print(temp)
                    breakdown = temp.split()
                    if(len(breakdown)==1): #no surname or name, something is broken
                        x[it+1] = temp+" "+x[it+1] #add it to the next
                    else:
                        #temp=temp.strip() #after replacement some still have whitespace
                        #APPEND W TYM MIEJSCU DOSŁOWNIE NIE DZIAŁA, ANI DODAWANIE DO LISTY TEZ, NIE WIEM CZEMU ALE OMIJA 5 POSLOW TAK Z DUPY
                        #print(temp)
                        for str in firstBreak:
                            if(str!=''):
                                str=str.strip()
                                newString=newString+str+"|"
                else:
                    #print(f"{temp} passed this value ")
                    pass
                   
                        #count=count+1
        it=it+1
    #print(newString)
    return(newString, partyList)


def WrapPDFParty(response):
    with io.BytesIO(response.content) as file:
        try:
            parser = PDFParser(file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            output_string=io.StringIO()
            device = TextConverter(rsrcmgr,output_string,laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)
            page_content = output_string.getvalue()
            tempString, partyList =namePartyParser(page_content)
            tempNames=tempString.split('|')
            tempNames.pop()#last line is empty
            print(partyList)
            zit=0
            for z in partyList:
                for i in range(1,z[1]+1):
                    #print(zit)
                    #print(f"posel no.{zit+1} {tempNames[zit]} belongs to {z[0]}")
                    #str=f"INSERT INTO PARTIES (NAME, PARTY) VALUES ('{tempNames[zit]}','{z[0]}');"
                    #str=f"INSERT INTO PARTIES (PARTY1) VALUES ('{z[0]}') WHERE NAME = '{tempNames[zit]}';"
                    str=f"UPDATE PARTIES SET PARTY1='{z[0]}' where NAME='{tempNames[zit]}' IF @@ROWCOUNT=0 INSERT INTO PARTIES(NAME, PARTY1) values('{tempNames[zit]}','{z[0]}');"
                    zit=zit+1
                    try:
                        cursor.execute(str)
                    except Exception as e:
                        print(e)
                    else:
                        pass
                #print(f"{z} belongs to {tempParties[zit]}")
            cursor.commit()
        except Exception as e:
            print("exception catched")
            print(e)
        else:
            pass


url= "http://orka.sejm.gov.pl/Glos9.nsf/dok?OpenAgent&1_2"
response = requests.get(url)
WrapPDFParty(response)