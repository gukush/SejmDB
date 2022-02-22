import pandas as pd
import requests
import io
import pyodbc
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

#functions for connecting to database (please input valid credentials and creation of sql table
some_pass = "MY_PASSWORD"
some_uid = "MY_USERNAME"
some_server = "MY_SERVER"
cnxn = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};"+f"Server={some_server};Database=SejmVote;UID={some_uid};PWD={some_pass}")
createCursor = cnxn.cursor()
createString = "IF NOT EXISTS (SELECT * FROM sys.tables WHERE NAME='VOTES') CREATE TABLE VOTES(NAME varchar(40), POS int, GLOS int, VAL int, PRIMARY KEY (NAME,POS,GLOS) )"
createCursor.execute(createString)
cnxn.commit

str ="SELECT POS, GLOS FROM VOTES"
createCursor.execute(str)
AlreadyInTable=createCursor.fetchall()


def uploadToDB2(nameList,voteList,pos,glos):
    it=0
    if(len(voteList)==0):
        raise ValueError("Vote list is empty")
    if(len(nameList)==len(voteList)):
        while it < len(voteList):
            str = f"INSERT INTO VOTES (NAME, POS, GLOS, VAL) VALUES ('{nameList[it]}',{pos},{glos},{voteList[it]});"
            createCursor.execute(str)
            it=it+1
    else:
        print(f"ERROR, unequal amount of things! there are {len(nameList)} entries for names and {len(voteList)} for votes instead of 460")
        raise ValueError("Unequal ammount of things")
    cnxn.commit()
    print(f"Updated database insertion of pos: {pos}, glos: {glos}")

def voteParser(myString):
    voteList=[]
    x=myString.split('\n')
    it=15
    while it < len(x):
        if(len(x[it])>40):
            it=it+1
        else:
            break
    merge =""
    merge = merge.join(x[it:])
    merge = merge.replace('pr.','#-1#')
    merge = merge.replace('za','#1#')
    merge = merge.replace('ws.',"#0#")
    merge = merge.replace('ng.',"#0#")
    x = merge.split('#')
    
    for item in x:
        print(item)
        if(len(item)<=2)and(item.lstrip('-').isdigit()):
            print(f"{item} it passes criteria")
            voteValue=int(item)
            voteList.append(voteValue)
    return voteList

def nameParser2(myString):
    nameList=[]
    newString=""
    x=myString.split('\n')
    count=0
    it=15
    while it < len(x):
        temp = x[it].strip()
        if(temp !=''):
            if any(c.isdigit() for c in temp):#or("(" in temp or ")" in temp)or(len(x)<4)or(len(x)>40):#or("Sejm" in temp)or("Pkt" in temp)or("Posiedzenie" in temp):
                pass
            elif len(temp)>3:#and len(temp)<=40:
                
                temp = temp.replace('pr.','#')
                temp = temp.replace('za','#')
                temp = temp.replace('ws.','#')
                temp = temp.replace('ng.','#')
                firstBreak = temp.split('#')
                if not any(c.islower() for c in temp):
                    print(temp)
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
                                #print(str)
                else:
                    #print(f"{temp} passed this value ")
                    pass
                   
                        #count=count+1
        it=it+1
    return(newString)

#getting the table of votes per meeting into pandas
url = "https://www.sejm.gov.pl/Sejm9.nsf/agent.xsp?symbol=posglos&NrKadencji=9"
html = requests.get(url).content
html_tables = pd.read_html(html)
df = html_tables[0]
#making dataframe more useful
df.drop(columns=['Data pos. Sejmu','Unnamed: 3'],inplace=True)
df.columns = ['num','cnt']
df = df.fillna(method='ffill')
df['num'] = df['num'].astype(int)
df2 = df.groupby('num').sum()
df2['cnt']=df2['cnt'].astype(int)

notSupportedVotes=[]

def WrapPDF(response,i,j,tempNames):
    with io.BytesIO(response.content) as file:
        try:
            #pdf = PyPDF2.PdfFileReader(file)
            #numpages = pdf.getNumPages()
            #for k in range(0,numpages):
            #    page = pdf.getPage(k)
            #    page_content = page.extractText()
            #    print(page_content)
            #    g = myParser(page_content,i,j)
            #    uploadToDB(g)
            #print(page_content)
            parser = PDFParser(file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            output_string=io.StringIO()
            device = TextConverter(rsrcmgr,output_string,laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)
            page_content = output_string.getvalue()
            if(j==1)or(len(tempNames)==0):
                tempString=nameParser2(page_content)
                tempNames=tempString.split('|')
                tempNames.pop()#last line is empty
                for z in tempNames:
                    print(z)

            if(len(tempNames)!=0):
                votes = voteParser(page_content)
                uploadToDB2(tempNames,votes,i,j)
            else:
                raise ValueError("Name list is empty")

        except Exception as e:
            print(f"tego glosowania nie udalo sie zdobyc: pos:{i} glos:{j}")
            print(e)
            notSupportedVotes.append(f"pos {i}, glos {j}")
            return tempNames
        else:
            pass
        return tempNames

tempNames=[]
cnt=0
TableIsNotEmpty = True
if not AlreadyInTable:
    TableIsNotEmpty = False

for i, row in df2.iterrows():
    for j in range(1,row['cnt']):
        if(TableIsNotEmpty)and(i==AlreadyInTable[cnt][0])and(j==AlreadyInTable[cnt][1]):
            cnt=cnt+1
        else:
            if(i>=1)and(j>=1):
                url = f"http://orka.sejm.gov.pl/Glos9.nsf/dok?OpenAgent&{i}_{j}"
                response = requests.get(url)
                tempNames = WrapPDF(response,i,j,tempNames)
        

for item in notSupportedVotes:
    print(item)
