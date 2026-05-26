#shogi.py ますクラス、将棋クラス、駒クラスの定義
from itertools import product

PIECE_ORDER = ["歩", "香", "桂", "銀", "金", "角", "飛"]

fst,snd="first","second"
mix='mix'


class Masu:
    def __init__(self,i,j):
        self.__sit = False
        self.rch = {fst:[],snd:[]}
        self.str_owner=''
        self.pos=[i,j]
        if i==0:
            self.str_rtn="\n　"
        else:
            self.str_rtn=' '

    def get_koma(self):
        return(self.__sit)

    def pop_koma(self):
        koma = self.__sit
        self.__sit = False
        return(koma)

    def isOpen(self):
        return(not self.__sit)

    def get_sitting_debug(self):
        if self.__sit:
            return self.str_rtn+self.str_owner+self.__sit.char+"　,"
        else:    
            return self.str_rtn+" - 　,"

    def get_reach_debug(self,fs):
        txt=''
        blank=' '
        n=len(self.rch[fs])
        if n<4:
            for i in self.rch[fs]:
                txt=txt+i.char
            for i in range(3-n):
                txt=txt+blank
        else:
            for i in range(3):
                txt=txt+self.rch[fs][i].char
        return self.str_rtn+txt+','
    
    def set_koma(self,koma):
        if self.__sit:
            print('Error! koma already exists! x,y='+str(koma.pos))
            return
        self.__sit=koma
        koma.pos=self.pos
        if koma.owner==fst:
            self.str_owner="▲"
        elif koma.owner==snd:
            self.str_owner="▼"
        #print('Masu:set_koma', koma.char,self.pos,koma.owner,self.__sit)

class Shogi:
    komadic={'龍':'飛','馬':'角','全':'銀','圭':'桂','杏':'香','と':'歩'}
    def __init__(self):
        self.distrib={fst:[],snd:[],mix:[]}
        self.ban=[ [Masu(i,j) for j in range(9)]for i in range(9)]
        self.kdai={fst:{'歩':[],'飛':[],'角':[],'香':[],'桂':[],'銀':[],'金':[]}
                  ,snd:{'歩':[],'飛':[],'角':[],'香':[],'桂':[],'銀':[],'金':[]}}
        self.kban={fst:[] , snd:[]}
        self.FuDic={fst:[False for i in range(9)],snd:[False for i in range(9)]}

    def get_debug_ban(self):
        txt,txt_fr,txt_sr = '','',''
        for j in range(9):
            for i in range(9):
                txt=txt+self.ban[i][j].get_sitting_debug()
                txt_fr=txt_fr+self.ban[i][j].get_reach_debug(fst)
                txt_sr=txt_sr+self.ban[i][j].get_reach_debug(snd)
        return txt,txt_fr,txt_sr

    def remove_reach(self,koma):
        #print('remove_reach:' , koma,koma.rch)
        #print('remove_reach', self.ban[5][1].rch)
        for x,y in koma.rch:
            #print('x,y=',x,y)
            self.ban[x][y].rch[koma.owner].remove(koma)
        koma.rch=[]
        
    def reset_reach_all(self):
        for i in range(9):
            for j in range(9):
                self.ban[i][j].rch[fst]=[]
                self.ban[i][j].rch[snd]=[]
        
    def gen_komas(self):
        for i in range(18):
            km=Fu(0,0,snd)
            self.kdai[snd][km.char].append(km)
        for i in range(4):
            km=Kin(0,0,snd)
            self.kdai[snd][km.char].append(km)
        for i in range(4):
            km=Gin(0,0,snd)
            self.kdai[snd][km.char].append(km)
        for i in range(4):
            km=Kei(0,0,snd)
            self.kdai[snd][km.char].append(km)
        for i in range(4):
            km=Kyo(0,0,snd)
            self.kdai[snd][km.char].append(km)
        for i in range(2):
            km=Hisha(0,0,snd)
            self.kdai[snd][km.char].append(km)
        for i in range(2):
            km=Kaku(0,0,snd)
            self.kdai[snd][km.char].append(km)
        self.Gyoku = Gyoku(4,0,snd)
        self.ban[4][0].set_koma(self.Gyoku)
        self.kban[snd].append(self.Gyoku)

    def put_koma(self,owner,kmchar,x,y):
        if self.kdai[owner][kmchar]==[]:
            print('Error!'+owner+kmchar+'not exist.')
        else:
            km=self.kdai[owner][kmchar].pop()
            self.kban[owner].append(km)
            if self.ban[x][y].isOpen:
                self.ban[x][y].set_koma(km)
            else:
                print('Error Shogi:put_koma masu[xy] is not open',x,y)
            if km.char == '歩':
                self.FuDic[owner][km.pos[0]]=True

    def warp_koma(self,koma,x,y):
        x0,y0=koma.pos
        km = self.ban[x0][y0].pop_koma()
        self.ban[x][y].set_koma(km)

    def ban2dai_koma(self,koma,owner):
        x0,y0=koma.pos
        km = self.ban[x0][y0].pop_koma()
        self.kban[km.owner].remove(km)
        km.chg_owner(owner)
        km.reset()
        self.kdai[owner][koma.char].append(km)

    def change_owner_ban(self,x,y):
        km=self.ban[x][y].get_koma()
        owner=km.owner
        if(owner==fst):
            km.chg_owner(snd)
            self.kban[fst].remove(km)
            self.kban[snd].append(km)
        elif(owner==snd):
            km.chg_owner(fst)
            self.kban[snd].remove(km)
            self.kban[fst].append(km)

    def change_owner_kdai(self,frmOwn,toOwn,char):
        km=self.kdai[frmOwn][char].pop()
        self.kdai[toOwn][char].append(km)
        km.chg_owner(toOwn)
        return

    def extend_reach_all(self):
        self.reset_reach_all()    #すべてのマスのrch辞書の中のリストをクリアする。

        self.__gen_distrib()    #軍勢配置リストのDictionaryを作成する。
        
        self.updateFuDic()  #ver1.2で修正、不具合修正
        
        for km in self.kban[fst]:
            self.extend_reach(km,self.distrib[mix])
        for km in self.kban[snd]:
            self.extend_reach(km,self.distrib[mix])

    def __gen_distrib(self):
        self.distrib={fst:[],snd:[],mix:[]}
        for owr in self.kban.keys():
            for ikoma in self.kban[owr]:
                self.distrib[owr].append(ikoma.pos)
                self.distrib[mix].append(ikoma.pos)

    def updateFuDic(self):
        for owner in [fst,snd]:
            for ix in range(9):
                self.FuDic[owner][ix]=False
            for km in self.kban[owner]:
                if km.char=='歩':
                    self.FuDic[owner][km.pos[0]]=True

    def extend_reach(self,koma,mixdist):
        koma.gen_reach(mixdist)
        for x,y in koma.rch:
            self.ban[x][y].rch[koma.owner].append(koma)

    def DoOperation(self,ope):
        #print('Shogi:DoOperation',ope.owner,ope.char,ope.fromPos,'→',ope.toPos,'打ち',ope.isUchi,'成',ope.isNari)
        if ope.char == '金' and ope.toPos == self.Gyoku.pos:
            print('error')
        if ope.isUchi:
            x,y=ope.toPos
            self.put_koma(ope.owner,ope.char,x,y)
            self.__gen_distrib()
            self.extend_reach(self.ban[x][y].get_koma(),self.distrib[mix])
            for ikoma in self.ban[x][y].rch[fst]+self.ban[x][y].rch[snd]:   #駒を打ったことによってcanFly駒の効きがなくなる場合も考慮必要
                if ikoma.canFly:
                    self.remove_reach(ikoma)
                    self.extend_reach(ikoma,self.distrib[mix])
        else:
            x,y=ope.fromPos
            koma=self.ban[x][y].get_koma()
            self.Game_move_koma(koma, ope.toPos,ope.isNari)
        return

    def Game_move_koma(self,koma,topos,Nari):
        self.remove_reach(koma)
        x,y=koma.pos
        self.ban[x][y].pop_koma()
        xd,yd=topos
        if not self.ban[xd][yd].isOpen():    #相手の駒をとるとき。
            ckoma=self.ban[xd][yd].pop_koma()
            if ckoma.char=='歩': #FuDicのメンテナンス
                self.FuDic[ckoma.owner][xd]=False
            if ckoma.owner == koma.owner:
                print('error')  #（自分の駒ではない前提）
            self.remove_reach(ckoma)    #とられる駒のrchをクリアする。盤のechも。
            self.kban[ckoma.owner].remove(ckoma)
            ckoma.chg_owner(koma.owner)
            ckoma.reset()
            self.kdai[koma.owner][ckoma.char].append(ckoma)
        if Nari:
            if koma.char=='歩': #FuDicのメンテナンス
                self.FuDic[koma.owner][xd]=False
            koma.promote()
        self.ban[xd][yd].set_koma(koma)
        self.__gen_distrib()
        self.extend_reach(koma,self.distrib[mix])
        for ikoma in self.ban[x][y].rch[fst] + self.ban[x][y].rch[snd]:    #動いたことで駒の効き道が通るときの考慮
            if ikoma != koma and ikoma.canFly: #自分自身は除く
                #print("rch リセット必要", ikoma.char, ikoma.pos)
                poslst = ikoma.extend_rch(self.distrib[mix])
                for x,y in poslst:
                    self.ban[x][y].rch[ikoma.owner].append(ikoma)
        for ikoma in self.ban[xd][yd].rch[fst]+self.ban[xd][yd].rch[snd]:#同様に移動したことによってcanFly駒の効きがなくなる場合も考慮必要
            if ikoma.canFly:
                self.remove_reach(ikoma)
                self.extend_reach(ikoma,self.distrib[mix])
        #self.__gen_distrib() 重複処理になるので削除

    def move_koma(self,koma,topos,Nari):
        self.remove_reach(koma)
        x,y=koma.pos
        self.ban[x][y].pop_koma()
        xd,yd=topos
        if not self.ban[xd][yd].isOpen():
            raise Exception
        if Nari:
            koma.promote()
        self.ban[xd][yd].set_koma(koma)

        return
    
    def copy(self):
        shgcpy=Shogi()
        shgcpy.gen_komas()
        #Gyoku
        x,y=self.Gyoku.pos
        shgcpy.warp_koma(shgcpy.Gyoku,x,y)
        #snd koma
        for skoma in self.kban[snd]:
            if skoma.char=='玉':
                continue
            x,y=skoma.pos
            if skoma.ispromoted:
                shgcpy.put_koma(snd,Shogi.komadic[skoma.char],x,y)
                shgcpy.ban[x][y].get_koma().promote()
            else:
                shgcpy.put_koma(snd,skoma.char,x,y)
        #fst koma ban
        for fkoma in self.kban[fst]:
            x,y=fkoma.pos
            if fkoma.ispromoted:
                shgcpy.change_owner_kdai(snd,fst,Shogi.komadic[fkoma.char])
                shgcpy.put_koma(fst,Shogi.komadic[fkoma.char],x,y)
                shgcpy.ban[x][y].get_koma().promote()
            else:
                shgcpy.change_owner_kdai(snd,fst,fkoma.char)
                shgcpy.put_koma(fst,fkoma.char,x,y)
        #fst koma dai
        for fkomachar in self.kdai[fst]:
            for fkoma in self.kdai[fst][fkomachar]:
                shgcpy.change_owner_kdai(snd,fst,fkomachar)
        #extend reach all
        shgcpy.extend_reach_all()
        
        return shgcpy
    
    def count_komadai(self,owner):
        nkoma = 0
        for char in self.kdai[owner]:
            nkoma += len(self.kdai[owner][char])
            
        return nkoma
    
    def isBlocking(self,koma):
        x,y = koma.pos
        rchlst = self.ban[x][y].rch[fst]
        for i in rchlst:
            if i.canFly:
                outerCells = i.getOuterCells(koma.pos)
                for cell in outerCells:
                    xc,yc=cell
                    if self.ban[xc][yc].isOpen():
                        continue
                    elif self.ban[xc][yc].get_koma() == self.Gyoku:
                            return i
                    else:
                        break
        return False
    
    def isChecked(self):
        x,y = self.Gyoku.pos
        return self.ban[x][y].rch[fst]!=[]

    def isDaiEmpty(self,owner):
        for char in self.kdai[owner]:
            if self.kdai[owner][char]:
                return False
        return True

    def get_string_ban(self, owner):
        # owner の盤上の駒を位置 (y, x) でソート
        sorted_kban = sorted(self.kban[owner], key=lambda k: (k.pos[1], k.pos[0]))

        # 例: "S歩11,S金39,G銀28" のような形式
        s = []
        for koma in sorted_kban:
            ox = koma.pos[0]
            oy = koma.pos[1]
            s.append(f"{koma.char}{ox}{oy}")
        return ",".join(s)

    def get_string_kdai(self, owner):
        order = ['歩','香','桂','銀','金','角','飛']
        s = []
        for k in order:
            count = len(self.kdai[owner][k])
            s.append(f"{k}{count}")
        return ",".join(s)

    def __repr__(self):
        f_ban = self.get_string_ban(fst)
        g_ban = self.get_string_ban(snd)
        f_dai = self.get_string_kdai(fst)

        return f"{f_ban}|{g_ban}|{f_dai}"

    def parse_hand_string(self,hand_str):
        """
        "歩0,香0,桂1,銀1,金0,角0,飛0"
            → {"歩":0, "香":0, ...}
        """
        hand = {}
        for item in hand_str.split(","):
            piece = item[0]
            num = int(item[1:])
            hand[piece] = num
        return hand

    def hand_to_string(self,hand_dict):
        """
        {"歩":0, "香":0, ...}
            → "歩0,香0,桂1,銀1,金0,角0,飛0"
        """
        return ",".join(f"{p}{hand_dict[p]}" for p in PIECE_ORDER)

    def generate_fullkey_subsets(self,fullkey):
        """
        入力:
            "龍51,歩64|桂70,玉80,歩83|歩0,香0,桂1,銀1,金0,角0,飛0"
        出力:
            [
                "龍51,歩64|桂70,玉80,歩83|歩0,香0,桂0,銀0,金0,角0,飛0",
                ...
            ]
            ※元の持ち駒と一致するものは除外
        """
        # 3つに分割
        board_sente, board_gote, hand_str = fullkey.split("|")

        # 持ち駒を dict に変換
        original = self.parse_hand_string(hand_str)

        # 各駒種ごとに 0〜元の枚数 の範囲を作る
        ranges = [range(original[p] + 1) for p in PIECE_ORDER]

        subsets = []
        for combo in product(*ranges):
            subset = {p: combo[i] for i, p in enumerate(PIECE_ORDER)}

            # 元の持ち駒と完全一致なら除外
            if all(subset[p] == original[p] for p in PIECE_ORDER):
                continue

            subsets.append(subset)

        # 合計枚数が少ない順にソート（冗長手排除に有効）
        subsets.sort(key=lambda d: sum(d.values()))

        # フルキー形式に変換
        fullkeys = []
        for s in subsets:
            new_hand_str = self.hand_to_string(s)
            new_fullkey = f"{board_sente}|{board_gote}|{new_hand_str}"
            fullkeys.append(new_fullkey)

        return fullkeys





class Koma:
    dir_G={"first":[[0,-1,1],[-1,-1,1],[1,-1,1],[-1,0,1],[1,0,1],[0,1,1]],"second":[[0,1,1],[-1,1,1],[1,1,1],[-1,0,1],[1,0,1],[0,-1,1]]}
    dir_S={"first":[[0,-1,1],[-1,-1,1],[1,-1,1],[-1,1,1],[1,1,1]],"second":[[0,1,1],[-1,1,1],[1,1,1],[-1,-1,1],[1,-1,1]]}
    dir_N={"first":[[-1,-2,1],[1,-2,1]],"second":[[-1,2,1],[1,2,1]]}
    dir_L={"first":[[0,-1,8]],"second":[[0,1,8]]}
    dir_P={"first":[[0,-1,1]],"second":[[0,1,1]]}
    dir_R=[[0,-1,8],[0,1,8],[-1,0,8],[1,0,8]]
    dir_PR= [[0,-1,8],[0,1,8],[-1,0,8],[1,0,8],[-1,-1,1],[-1,1,1],[1,-1,1],[1,1,1]]
    dir_B= [[-1,-1,8],[1,-1,8],[-1,1,8],[1,1,8]]
    dir_PB= [[-1,-1,8],[1,-1,8],[-1,1,8],[1,1,8],[0,-1,1],[0,1,1],[-1,0,1],[1,0,1]]

    dir_R_d={'first':dir_R,'second':dir_R}
    dir_PR_d={'first':dir_PR,'second':dir_PR}
    dir_B_d={'first':dir_B,'second':dir_B}
    dir_PB_d={'first':dir_PB,'second':dir_PB}
 
    dicdir={'金':dir_G,'銀':dir_S,'桂':dir_N,'香':dir_L,'歩':dir_P,'飛':dir_R_d,'角':dir_B_d,'龍':dir_PR_d,'馬':dir_PB_d,'全':dir_G,'圭':dir_G,'杏':dir_G,'と':dir_G}

    def __init__(self,x,y,owner):
        self.pos = [x,y]
        self.owner = owner
        self.char = "金"
        self.dir = self.dir_G[owner]
        self.rch=[]
        self.pchar=None
        #self.prch=False
        self.ispromoted=False
        self.canFly= False

    def __repr__(self) -> str:
        return self.char

    def chg_owner(self,owner):
        self.owner=owner
        self.reset()

    def gen_reach(self,mixdist):
        self.rch = self.sub_gen_reach(mixdist,self.dir)

    def sub_gen_reach(self,mixdist,dir):
        rch=[]
        for xdr,ydr,n in dir:
            if n==1:
                rch0 = [self.pos[0]+xdr,self.pos[1]+ydr]
                if not (rch0[0]<0 or rch0[0]>8 or rch0[1]<0 or rch0[1]>8):
                    rch.append(rch0)
            else:
                #print('debug gen_reach: Fly')
                rch.extend(self.__gen_reachFly(xdr,ydr,n,mixdist))
        return rch

    def __gen_reachFly(self, xdr,ydr,n,mixdist):
        retrch=[]
        for i in range(1,n+1):
            rch0 = [self.pos[0]+xdr*i,self.pos[1]+ydr*i]
            #print('debug __gen_reachFly  rch0=',rch0)
            if not (rch0[0]<0 or rch0[0]>8 or rch0[1]<0 or rch0[1]>8):
                if rch0 in mixdist:
                    retrch.append(rch0)
                    #print('debug __gen_reachFly  find in mixlist rch0=' ,rch0)
                    return retrch
                else:
                    retrch.append(rch0)
            else:
                return retrch
        return retrch

    def extend_rch(self,mixdist):
        retlst=[]
        for xdr,ydr,n in self.dir:
            if n==1:
                break
            else:
                #print('debug_reset_rch',self.char, self.dir)
                for i in range(1,n+1):
                    rch0 = [self.pos[0]+xdr*i,self.pos[1]+ydr*i]
                    if not (rch0[0]<0 or rch0[0]>8 or rch0[1]<0 or rch0[1]>8):
                        if rch0 in self.rch:
                            if rch0 in mixdist:
                                break
                            pass
                        elif rch0 in mixdist:
                            self.rch.append(rch0)
                            retlst.append(rch0)
                            #print('debug_reset_rch*',rch0,'駒ありbreak')
                            break
                        else:
                            self.rch.append(rch0)
                            retlst.append(rch0)
                            #print('debug_reset_rch*',rch0,'駒なし、続く')
                    else:
                        break
        return retlst
                        
        
                

    def reset(self):    #(1)成った状態から戻す。(2)dirをOwnerに応じてセットしなおす
        self.ispromoted=False
        self.dir = self.dir_G[self.owner]

    
    def promote(self):
        self.ispromoted=True
    
class Kin(Koma):
    def __init__(self,x,y,owner):
        super().__init__(x,y,owner)
        self.char = "金"    
        
    def promote(self):
        pass
    
    def reset(self):
        super().reset()

class Gin(Koma):
    def __init__(self,x,y,owner):
        super().__init__(x,y,owner)
        self.reset()
        
    def reset(self):
        self.char = "銀"
        self.pchar="全"
        self.dir = self.dir_S[self.owner]
        self.ispromoted=False

    def promote(self):
        self.char = "全"
        self.dir = self.dir_G[self.owner]
        self.ispromoted=True
        
class Kei(Koma):
    def __init__(self,x,y,owner):
        super().__init__(x,y,owner)
        self.reset()
        
    def reset(self):
        self.char = "桂"
        self.pchar="圭"
        self.dir = self.dir_N[self.owner]
        self.ispromoted=False
       
    def promote(self):
        self.char = "圭"
        self.dir = self.dir_G[self.owner]
        self.ispromoted=True

class Kyo(Koma):
    def __init__(self,x,y,owner):
        super().__init__(x,y,owner)
        self.reset()
        
    def reset(self):
        self.char = "香"
        self.pchar="杏"
        self.dir = self.dir_L[self.owner]
        self.ispromoted=False
        self.canFly = True

    def promote(self):
        self.char = "杏"
        self.dir = self.dir_G[self.owner]
        self.ispromoted=True
        self.canFly=False

    def getOuterCells(self,pos):
        if self.ispromoted:
            return False
        if self.pos[0]==pos[0]:
            if self.pos[1] < pos[1]:
                e=[0,1]
            else:
                e=[0,-1]
        else:
            return []
        
        ocells=[]
        for i in range(1,9):
            x,y = pos[0]+e[0]*i,pos[1]+e[1]*i
            if x<0 or x>8 or y<0 or y>8:
                break
            else:
                ocells.append([x,y])
        
        return ocells
    
    def getInnerCells(self,pos):
        if self.ispromoted:
            return False
        if self.pos[0]==pos[0]:
            if self.pos[1] < pos[1]:
                e=[0,1]
            else:
                e=[0,-1]
        else:
            return []
        
        icells=[]
        for i in range(1,9):
            x,y = self.pos[0]+e[0]*i,self.pos[1]+e[1]*i
            if x==pos[0] and y==pos[1]:
                break
            else:
                icells.append([x,y])
        
        return icells

class Fu(Koma):
    def __init__(self,x,y,owner):
        super().__init__(x,y,owner)
        self.reset()
        
    def reset(self):
        self.char = "歩"
        self.pchar="と"
        self.dir = self.dir_P[self.owner]
        self.ispromoted=False

    def promote(self):
        self.char = "と"
        self.dir = self.dir_G[self.owner]
        self.ispromoted=True

class Hisha(Koma):
    def __init__(self,x,y,owner):
        super().__init__(x,y,owner)
        self.reset()
        self.canFly=True
        
    def reset(self):
        self.char = "飛"
        self.pchar="龍"
        self.dir = self.dir_R
        self.ispromoted=False

    def promote(self):
        self.char = "龍"
        self.dir = self.dir_PR
        self.ispromoted=True
    
    def getOuterCells(self,pos):
        if self.pos[0]==pos[0]:
            if self.pos[1] < pos[1]:
                e=[0,1]
            else:
                e=[0,-1]
        elif self.pos[1]==pos[1]:
            if self.pos[0] < pos[0]:
                e=[1,0]
            else:
                e=[-1,0]
        else:
            return []
        
        ocells=[]
        for i in range(1,9):
            x,y = pos[0]+e[0]*i,pos[1]+e[1]*i
            if x<0 or x>8 or y<0 or y>8:
                break
            else:
                ocells.append([x,y])
        
        return ocells
    
    def getInnerCells(self,pos):
        if self.pos[0]==pos[0]:
            if self.pos[1] < pos[1]:
                e=[0,1]
            else:
                e=[0,-1]
        elif self.pos[1]==pos[1]:
            if self.pos[0] < pos[0]:
                e=[1,0]
            else:
                e=[-1,0]
        else:
            return []
        
        icells=[]
        for i in range(1,9):
            x,y = self.pos[0]+e[0]*i,self.pos[1]+e[1]*i
            if x==pos[0] and y==pos[1]:
                break
            else:
                icells.append([x,y])
        
        return icells

class Kaku(Koma):
    def __init__(self,x,y,owner):
        super().__init__(x,y,owner)
        self.reset()
        
    def reset(self):
        self.char = "角"
        self.pchar="馬"
        self.dir = self.dir_B
        self.ispromoted=False
        self.canFly=True

    def promote(self):
        self.char = "馬"
        self.dir = self.dir_PB
        self.ispromoted=True
    
    def getOuterCells(self,pos):
        if self.pos[0]+self.pos[1]==pos[0]+pos[1]:
            if self.pos[0]-self.pos[1] < pos[0]-pos[1]:
                e=[1,-1]
            else:
                e=[-1,1]
        elif self.pos[0]-self.pos[1] == pos[0]-pos[1]:
            if self.pos[0]+self.pos[1]<pos[0]+pos[1]:
                e=[1,1]
            else:
                e=[-1,-1]
        else:
            return []
        
        ocells=[]
        for i in range(1,7):
            x,y = pos[0]+e[0]*i,pos[1]+e[1]*i
            if x<0 or x>8 or y<0 or y>8:
                break
            else:
                ocells.append([x,y])
        
        return ocells

    def getInnerCells(self,pos):
        if self.pos[0]+self.pos[1]==pos[0]+pos[1]:
            if self.pos[0]-self.pos[1] < pos[0]-pos[1]:
                e=[1,-1]
            else:
                e=[-1,1]
        elif self.pos[0]-self.pos[1] == pos[0]-pos[1]:
            if self.pos[0]+self.pos[1]<pos[0]+pos[1]:
                e=[1,1]
            else:
                e=[-1,-1]
        else:
            return []
        
        icells=[]
        for i in range(1,9):
            x,y = self.pos[0]+e[0]*i,self.pos[1]+e[1]*i
            if x==pos[0] and y==pos[1]:
                break
            else:
                icells.append([x,y])

        return icells

class Gyoku(Koma):
    def __init__(self,x,y,owner):
        super().__init__(x,y,owner)
        self.char = "玉"
        self.dir = [[0,-1,1],[-1,-1,1],[1,-1,1],[-1,0,1],[1,0,1],[-1,1,1],[1,1,1],[0,1,1]]

    def gen_chkposlst(self,char,mixdist):
        dir_chr=self.dicdir[char][snd]
        ret=self.sub_gen_reach(mixdist,dir_chr)
        
        if self.pos in ret:
            print('error')

        return ret

    def promote(self):
        pass
    
    def reset(self):
        pass
