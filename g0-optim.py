# Autor: Daniel Korczok 2023

from array import *
import sys
import math
import os
import argparse


parser=argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("-v", "--verbose", action="store_true")
group.add_argument("-q", "--quiet", action="store_true")
parser.add_argument("-F","--keepF", action="store_true",help="Keep speed information")
parser.add_argument('input', metavar="input_path",type=str,help="Path to file containing input gcode")
parser.add_argument('output', metavar="output_path",type=str,help="Path to desired output location (default: [input_file]_optim.gcode in the input file directory)",nargs='?',default=argparse.SUPPRESS)
args=parser.parse_args()
#zamienić plik na liste
unit="mm"
i=0
lista=[]
plik=args.input
with open(plik,encoding='utf8') as f:
    while True:
        lista.append(f.readline())
        if not lista[i]:
            break
        i=i+1

if hasattr(args,'output'):
    nazwa=args.output
else:
    if plik.startswith(".\\"):
        plik=plik[2:]
    index=plik.find(".gcode")
    nazwa=plik[:index]+'_optim'+plik[index:]

#odseparować ze spacją
#ruchy do osobnej listy:
#   typ ruchu
#   początek ruchu
#   koniec ruchu
#   promien (dla G1 G0 zostawie puste)
ruchy=[]
ruchyIndex=[] #indeks linii z ruchami
startX=float(0)
startY=float(0)
length=len(lista)
for i,linia in enumerate(lista):
    F=0
    if args.verbose:
        if i%100==0:
            print("Odczyt: {0}/{1}".format(i,length),end="\r")
    ruch=linia.replace(';',' ').split()
    if len(ruch)>1:
        if linia.startswith('N'):
            offset=0
        else:
            offset=-1
        if ruch[1+offset]=='G20':
            unit="in"
        if ruch[1+offset]=='G1' or ruch[1+offset]=='G0' or ruch[1+offset]=='G2' or ruch[1+offset]=='G3':
            ruchyIndex.append(i)
            X=round(float(ruch[2+offset].lstrip("X")),6)
            Y=round(float(ruch[3+offset].lstrip('Y')),6)
            if(ruch[1]=='G2' or ruch[1]=='G3'):
                R=round(float(ruch[4+offset].lstrip('R')),6)
                if len(ruch)>5+offset and ruch[5+offset].startswith('F'):
                    F=float(ruch[5+offset].lstrip('F'))
            else:
                R=float(0)
                if len(ruch)>4+offset and ruch[4+offset].startswith('F'):
                    F=float(ruch[4+offset].lstrip('F'))
            if math.floor(F)==F:
                F=int(F)
            ruchy.append([ruch[1+offset],startX,startY,X,Y,R,F])
            startX=X
            startY=Y
if args.verbose:
    print("Odczyt: {0}/{0}".format(length))
bloki=[]#bloki ruchów interpolowanych oddzielonymi ruchami G0
#startBloku,koniecBloku,początekIndex
for i,ruch in enumerate(ruchy):
    if ruch[0]=="G0":
        if i>0:
            bloki.append([startIndex,endIndex,startX,startY,endX,endY])
        startX=ruch[3]
        startY=ruch[4]
        startIndex=i+1
    endX=ruch[3]
    endY=ruch[4]
    endIndex=i
bloki.append([startIndex,endIndex,startX,startY,endX,endY])
print("{0} moves in {1} blocks".format(len(ruchy),len(bloki)))
#liczenie trasy przed optymalizacją
preOpti=float(0)
prevX=float(0)
prevY=float(0)
for blok in bloki:
    preOpti+=math.sqrt(pow(blok[2]-prevX,2)+pow(blok[3]-prevY,2))
    prevX=blok[4]
    prevY=blok[5]
preOpti=round(preOpti,2)
if not args.quiet:
    print("G0 przed optymalizają: {0}{1}".format(preOpti,unit))
#sortowanie bloków
blokiLen=len(bloki)
for i in range(len(bloki[:-1])):
    if args.verbose:
        if i%100==0:
            print("Optymalizowanie: {0}/{1}".format(i,blokiLen),end="\r")
    blok=bloki[i]
    trasy=[]
    for podblok in bloki[i+1:]:
        trasy.append([math.sqrt(pow(podblok[2]-blok[4],2)+pow(podblok[3]-blok[5],2))])
    minTrasa=min(trasy)
    j=trasy.index(minTrasa)
    if i+j+1<len(bloki):
        #print("{} {} {} {}".format(blok,minTrasa,j,bloki[i+j+1]))
        temp=bloki[i+j+1]
        bloki[i+j+1]=bloki[i+1]
        bloki[i+1]=temp
if args.verbose:
    print("Optymalizowanie: {0}/{0}".format(blokiLen))
#trasa po optymalizacji
postOpti=float(0)
prevX=float(0)
prevY=float(0)
for blok in bloki:
    postOpti+=math.sqrt(pow(blok[2]-prevX,2)+pow(blok[3]-prevY,2))
    prevX=blok[4]
    prevY=blok[5]
postOpti=round(postOpti,2)
if not args.quiet:
    print("G0 po optymalizacji: {0}{1}".format(postOpti,unit))
    print("Redukcja {}%".format(round((1-(postOpti/preOpti))*100,1)))
#zapis gkodu do pliku
n=1
out=""
if unit=="in":
    out+="N{} G20\n".format(n)
else:
    out+="N{} G21\n".format(n)
n+=1
out+="N{} G90\n".format(n)
n+=1
length=len(bloki)
for i,blok in enumerate(bloki):
    if args.verbose:
        if i%25==0:
            print("Zapis: {0}/{1}".format(i,length),end="\r")
    out+="N{} M5\n".format(n)
    n+=1
    out+="N{2} G0 X{0:f} Y{1:f} \n".format(blok[2],blok[3],n)
    n+=1
    out+="N{} M3\n".format(n)
    n+=1
    for i in range(blok[0],blok[1]+1,1):
        out+="N{3} {0} X{1:f} Y{2:f} ".format(ruchy[i][0],ruchy[i][3],ruchy[i][4],n)
        n+=1
        if ruchy[i][0]=="G2" or ruchy[i][0]=="G3":
            out+="R{:f} ".format(ruchy[i][5])
        if ruchy[i][6]>0 and args.keepF:
            out+="F{} ".format(ruchy[i][6])
        out+="\n"
out+="N{} M5\n".format(n)
n+=1
out+="N{} M2\n".format(n)
n+=1
if args.verbose:
    print("Zapis: {0}/{0}".format(length))
f=open(nazwa,'w')
f.write(out)
path=os.path.realpath(f.name)
f.close()
if not args.quiet:
    print("Gkod zapisano jako: {}".format(path))
