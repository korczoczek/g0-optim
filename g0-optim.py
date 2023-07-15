# Autor: Daniel Korczok 2023

from array import *
#import sys
import math
import os
import argparse


parser=argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
group = parser.add_mutually_exclusive_group()
group.add_argument("-v", "--verbose", action="store_true")
group.add_argument("-q", "--quiet", action="store_true")
parser.add_argument("-F","--keepF", action="store_true",help="Keep speed information")
parser.add_argument("-N","--lineNr",action="store_true",help="Generate line numbers")
parser.add_argument("-t","--trim", help="Amount of digits to keep after decimal point", default=6,type=int)
parser.add_argument("--toolon",type=str,default="M3",help="Tool On Sequence")
parser.add_argument("--tooloff",type=str,default="M5",help="Tool Off Sequence")
parser.add_argument("-b","--begin",type=str,default="",help="Program Begin Sequence")
parser.add_argument("-e","--end",type=str,default="",help="Program End Sequence")
parser.add_argument('input', metavar="input_path",type=str,help="Path to file containing input gcode")
parser.add_argument('output', metavar="output_path",type=str,help="Path to desired output location (default: [input_file]_optim.gcode in the input file directory)",nargs='?',default=argparse.SUPPRESS)
args=parser.parse_args()
#zamienić plik na liste
args.toolon=args.toolon.replace('\\n','\n')
args.tooloff=args.tooloff.replace('\\n','\n')
args.begin=args.begin.replace('\\n','\n')
args.end=args.end.replace('\\n','\n')
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
            print("Read: {0}/{1}".format(i,length),end="\r")
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
            X=round(float(ruch[2+offset].lstrip("X")),args.trim)
            Y=round(float(ruch[3+offset].lstrip('Y')),args.trim)
            if(ruch[1]=='G2' or ruch[1]=='G3'):
                R=round(float(ruch[4+offset].lstrip('R')),args.trim)
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
    print("Read: {0}/{0}".format(length))
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
if not args.quiet:
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
    print("G0 before optimization: {0}{1}".format(preOpti,unit))
#sortowanie bloków
blokiLen=len(bloki)
for i in range(len(bloki[:-1])):
    if args.verbose:
        if i%100==0:
            print("Optimizing: {0}/{1}".format(i,blokiLen),end="\r")
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
    print("Optimizing: {0}/{0}".format(blokiLen))
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
    print("G0 after optimization: {0}{1}".format(postOpti,unit))
    if args.verbose:
        print("{}% reduction of G0 movement".format(round((1-(postOpti/preOpti))*100,1)))
#zapis gkodu do pliku
out=""
if unit=="in":
    out+="G20\n"
else:
    out+="G21\n"
out+="G90\n"
if not args.begin=="":
    out+="{}\n".format(args.begin)
length=len(bloki)
for i,blok in enumerate(bloki):
    if args.verbose:
        if i%25==0:
            print("Write: {0}/{1}".format(i,length),end="\r")
    out+="{}\n".format(args.tooloff) #tool off
    out+="G0 X{0:f} Y{1:f} \n".format(blok[2],blok[3])
    out+="{}\n".format(args.toolon) #tool on
    for i in range(blok[0],blok[1]+1,1):
        out+="{0} X{1:f} Y{2:f} ".format(ruchy[i][0],ruchy[i][3],ruchy[i][4])
        if ruchy[i][0]=="G2" or ruchy[i][0]=="G3":
            out+="R{:f} ".format(ruchy[i][5])
        if ruchy[i][6]>0 and args.keepF:
            out+="F{:n} ".format(ruchy[i][6])
        out+="\n"
out+="{}\n".format(args.tooloff) #tool off
if not args.end=="":
    out+="{}\n".format(args.end)
out+="M2"#end gcode
if args.verbose:
    print("Write: {0}/{0}".format(length))
if args.lineNr:
    if not args.quiet:
        print("Generating line numbers")
    out2=""
    n=1
    for i,linia in enumerate(out.splitlines()):
        out2+="N{} {}\n".format(n,linia)
        n+=1
    out=out2

f=open(nazwa,'w')
f.write(out)
path=os.path.realpath(f.name)
f.close()
if not args.quiet:
    print("G-code saved as: {}".format(path))
