from operator import itemgetter

from shogi import fst,snd,mix

autoTestMode = False

class ListOperator:
    def andList(list1,list2):
        ret=[]
        for i in list1:
            if i in list2:
                ret.append(i)
        return ret

    def orList(list1,list2):
        ret=list1.copy()
        for i in list2:
            if not i in list1:
                ret.append(i)
        return ret

    def subList(list1,list2):
        ret=list1.copy()
        for i in list2:
            if i in ret:
                ret.remove(i)
        return ret

class Shogi_Operation:
    d_owner={fst:'▲',snd:'▽'}
    d_suji=('９','８','７','６','５','４','３','２','１')
    d_dan=('一','ニ','三','四','五','六','七','八','九')
    owner=''
    isUchi=False
    char=''
    isNari=False
    koma=None
    toPos=[]
    fromPos=[]
    
    def __init__(self,owner,uchi,char,nari,fpos,topos):
        self.owner=owner
        self.isUchi=uchi
        self.char=char
        self.isNari=nari
        self.toPos=topos
        self.fromPos=fpos
        
    def __repr__(self):
        player=Shogi_Operation.d_owner[self.owner]
        x,y=self.toPos
        pos=Shogi_Operation.d_suji[x]+Shogi_Operation.d_dan[y]
        ret=player+pos+self.char
        if self.isUchi:
            ret +='打'
        else:
            if self.isNari:
                ret +='成'
            ret += '  from'+str(self.fromPos)
        ret+='to'+str(self.toPos)
        return ret
    
 
nxt='next'
suc='success'
no='#'
