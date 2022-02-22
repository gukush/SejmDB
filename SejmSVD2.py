import pyodbc
import time
import pandas as pd
import numpy as np
some_pass = "MY_PASSWORD"
some_uid = "MY_USERNAME"
some_server = "MY_SERVER"
cnxn = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};"+f"Server={some_server};Database=SejmVote;UID={some_uid};PWD={some_pass}")
cursor = cnxn.cursor()
#getValidVotes="SELECT POS, GLOS FROM (SELECT DISTINCT POS, GLOS, COUNT(*) AS cnt FROM VOTES GROUP BY POS, GLOS) TEMP WHERE TEMP.cnt = 460 ORDER BY POS, GLOS"
#df = pd.read_sql(getValidVotes,cnxn)
#print(df.head())
#Different approach: ppl with max number of votes
#getHighestVoters="SELECT NAME, TEMP.cnt FROM (SELECT NAME, COUNT(*) AS cnt FROM VOTES GROUP BY NAME) TEMP WHERE cnt = (SELECT MAX(TEMP.cnt) FROM (SELECT NAME, COUNT(*) AS cnt FROM VOTES GROUP BY NAME) TEMP) ORDER BY NAME"
getHighestVoters="SELECT PARTIES.NAME, TEMP.cnt, PARTY1 FROM (SELECT NAME, COUNT(*) AS cnt FROM VOTES GROUP BY NAME) TEMP JOIN PARTIES ON TEMP.NAME=PARTIES.NAME WHERE cnt = (SELECT MAX(TEMP.cnt) FROM (SELECT NAME, COUNT(*) AS cnt FROM VOTES GROUP BY NAME) TEMP WHERE PARTY1!='PiS') ORDER BY NAME"
cursor.execute(getHighestVoters)
listOfVoters = cursor.fetchall()
numberOfVotes = listOfVoters[0][1]
print(numberOfVotes)
matrixOfVotes=np.empty((len(listOfVoters),numberOfVotes))

it=0
for row in listOfVoters:
    str=f"SELECT VAL FROM VOTES WHERE NAME='{row[0]}' ORDER BY POS, GLOS"
    cursor.execute(str)
    val = cursor.fetchall()
    val = [i[0] for i in val]
    matrixOfVotes[it] = np.asarray(val)
    it=it+1
#    print(val)
print(matrixOfVotes)

print(np.shape(matrixOfVotes))
#Center the matrix  
mean = matrixOfVotes.mean(axis=0)
centered = matrixOfVotes - mean
np.savetxt(f"votes{time.time()}.csv", centered, delimiter=",")
#Taken from https://gist.github.com/wangz10/ba54f89ebcad21b04beb95622679116c#file-pca_eigen_docomposition_np-py
variance_explained=[]
def pca(X):
  # Data matrix X, assumes 0-centered
  n, m = X.shape
  assert np.allclose(X.mean(axis=0), np.zeros(m))
  # Compute covariance matrix
  C = np.dot(X.T, X) / (n-1)
  # Eigen decomposition
  eigen_vals, eigen_vecs = np.linalg.eig(C)
  for i in eigen_vals:
      variance_explained.append(i/sum(eigen_vals))
  print(variance_explained)
  # Project X onto PC space
  X_pca = np.dot(X, eigen_vecs)
  #projection = np.dot(X, (eigen_vecs.T[:][:11]).T)
  return X_pca, eigen_vecs

pcaResult, eigen_vec = pca(centered)
np.save("pca.npy", pcaResult)
np.save("eigen_vec.npy",eigen_vec)