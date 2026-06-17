# 詰将棋ソルバー Cython高速化可能なパーツを切り出し
#  Cython化済み（SolverUtils_cy.cp312-win_amd64.pyd)
try:
    from shogi_cy import fst,snd,mix,Shogi
    print("⚡⚡Using Shogi from shogi_cy.pyd")
except:
    from shogi import fst,snd,mix,Shogi
    print("■Using Shogi from shogi.py")

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

        self.captured = None
        self.wascapNari = None
        
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
    
    # ★ 値としての同一性を表すキー
    def to_key(self):
        return (
            self.owner,
            self.char,
            self.isUchi,
            self.isNari,
            None if self.fromPos is None else tuple(self.fromPos),
            tuple(self.toPos),
        )

    # ★ 値として同じなら True
    def __eq__(self, other):
        if not isinstance(other, Shogi_Operation):
            return False
        return self.to_key() == other.to_key()

    # ★ 値として同じなら同じハッシュ値
    def __hash__(self):
        return hash(self.to_key())

class ListOperator:

    @staticmethod
    def andList(list1,list2):
        ret=[i for i in list1 if i in list2]
        return ret

    @staticmethod
    def subList(list1,list2):
        ret=[i for i in list1 if i not in list2]
        return ret



def SearchOute(shogi:Shogi):

    lst_moveOute = SearchMoveOute(shogi)
    lst_uchiOute = SearchUchiOute(shogi)
    lst_HirakiOute = SearchHirakiOute(shogi)
    
    # 開き王手と移動王手の重複している手を徐除去する
    lst_HirakiOute = [h for h in lst_HirakiOute if h not in lst_moveOute]

    retlst = lst_uchiOute+lst_moveOute+lst_HirakiOute

    return retlst

def SearchMoveOute(shogi:Shogi):
    OuteList = []

    # 盤上の先手駒のループ
    for ikoma in shogi.kban[fst]:
        rchlst = ikoma.rch
        rchlst = ListOperator.subList(rchlst,shogi.distrib[fst])
        # rchlst = set(rchlst)-distrib_f
        chkposlst = shogi.Gyoku.gen_chkposlst(ikoma.char,shogi.distrib[mix])
        chklst = ListOperator.andList(rchlst,chkposlst)
        # chklst = rchlst & chkposlst
        # self.dbgprint('__searchMoveOute'+ikoma.char+str(chklst))

        #成王手を先にする
        if ikoma.pchar and not ikoma.ispromoted:
            chkposlst = shogi.Gyoku.gen_chkposlst(ikoma.pchar,shogi.distrib[mix])
            chkposlst = ListOperator.subList(chkposlst,shogi.distrib[fst])
            # chkposlst = set(chkposlst)-distrib_f
            chklst2 = ListOperator.andList(rchlst,chkposlst)
            # chklst2 = rchlst & chkposlst
        
            for ipos in chklst2:
                if ikoma.pos[1]<3 or ipos[1]<3:
                    OuteList.append(Shogi_Operation(fst,False,ikoma.char,True,ikoma.pos,ipos))

        for ipos in chklst:
            if ipos == shogi.Gyoku.pos:
                print('error')
            OuteList.append(Shogi_Operation(fst,False,ikoma.char,False,ikoma.pos,ipos))

    # self.dbgprint('__searchMoveOute'+str(OuteList))
    return OuteList

def SearchUchiOute(shogi:Shogi):
    OuteList = []

    for ichar,komalist in shogi.kdai[fst].items():
        if not komalist:
            continue
        # 以下、持ち駒あるとき、持ち駒種類ごとに王手を抽出
        if ichar == '歩' and shogi.FuDic[fst][shogi.Gyoku.pos[0]]:
            continue   #二歩防止のため、候補手に入れない。打ち歩詰め防止は__VerifyOuteCandidateの詰み判定にて実施
        #　王手可能位置
        chkposlst=shogi.Gyoku.gen_chkposlst(ichar,shogi.distrib[mix])
        chkposlst=ListOperator.subList(chkposlst,shogi.distrib[mix])
        # chkposlst=set(Shogi.Gyoku.gen_chkposlst(ichar,Shogi.distrib[mix]))-distrib_m
        for ipos in chkposlst:
            OuteList.append(Shogi_Operation(fst,True,ichar,False,None,ipos))
    # self.dbgprint('SearchUchiOute'+str(OuteList))

    return OuteList

def SearchHirakiOute(shogi:Shogi):
    OuteList = []
    for ikoma in shogi.kban[fst]:
        flyer = shogi.isBlocking(ikoma)
        if flyer:
            waycells=flyer.getInnerCells(ikoma.pos)+flyer.getOuterCells(ikoma.pos)
            cells = ListOperator.subList(ikoma.rch,waycells+shogi.distrib[fst])
            # cells = set(ikoma.rch) - set(waycells+Shogi.distrib[fst])

            for cell in cells:
                if ikoma.pchar and not ikoma.ispromoted:    #成り優先
                    if ikoma.pos[1]<3 or cell[1]<3:
                        OuteList.append(Shogi_Operation(fst,False,ikoma.char,True,ikoma.pos,cell))

                if ikoma.char == '香' and cell[1]==0: #香が1段に移動する際には成らなければならない
                    pass
                elif ikoma.char=='桂' and cell[1]<2:    ##桂が1段・2段に移動する際には成らなければならない
                    pass
                else:
                    OuteList.append(Shogi_Operation(fst,False,ikoma.char,False,ikoma.pos,cell))
    #移動王手と重複することあり→__serchOuteで重複チェックして削除する。

    return OuteList

    
    # def __searchMoveOute_on_cell(self,Shogi,cell):
    #     OuteList = []
    #     x,y = cell
    #     komas = Shogi.ban[x][y].rch[fst] #cellに移動可能な駒のリスト

    #     for koma in komas:
    #         if koma.pos[1]<3 or cell[1]<3:  #成ることができる場所にいて
    #             if koma.pchar and not koma.ispromoted: #成ることができる場合
    #                 chkposlst = Shogi.Gyoku.gen_chkposlst(koma.pchar,Shogi.distrib[mix])
    #                 if cell in chkposlst:
    #                     OuteList.append(Shogi_Operation(fst,False,koma.char,True,koma.pos,cell))
    #         chkposlst = Shogi.Gyoku.gen_chkposlst(koma.char,Shogi.distrib[mix])
    #         if cell in chkposlst:
    #             OuteList.append(Shogi_Operation(fst,False,koma.char,False,koma.pos,cell))
        
    #     return OuteList


    # def searchUke(self,shogi):
    #     lst_Tori = self.__searchToriUke(shogi)
    #     lst_Nige = self.__searchNigeUke(shogi)
    #     lst_aigoma,mudaCandsLst = self.__searchAigoma(shogi)
    
    #     self.dbgprint('__searchUke'+str(lst_Nige+lst_Tori+lst_aigoma))
    #     return lst_Tori+lst_Nige+lst_aigoma,mudaCandsLst

    # def __searchNigeUke(self,shogi):
    #     xg,yg=shogi.Gyoku.pos
    #     outeKomaLst = shogi.ban[xg][yg].rch[fst]
    #     outeKomaPosLst=[]
    #     for ikoma in outeKomaLst:
    #         outeKomaPosLst.append(ikoma.pos)
        
    #     poslst = []
    #     for ipos in shogi.Gyoku.rch:
    #         x,y= ipos
    #         if (shogi.ban[x][y].rch[fst]==[]) and not (ipos in shogi.distrib[snd]): #相手の効きがなく、味方のいないところ
    #             if ipos not in outeKomaPosLst:  #同玉はToriukeで考慮済み。
    #                 poslst.append(ipos)
    #     #print('Solver:__searchNigeUke  poslst=',poslst)
        
    #     #飛車角香の効き延長を考慮、移動先が効きの延長線上であれば、この移動先はリストposlstから削除する。
    #     xg,yg=shogi.Gyoku.pos
    #     okomalst = shogi.ban[xg][yg].rch[fst]
    #     lst_canfly=[]
    #     for iok in okomalst:
    #         if iok.canFly:
    #             lst_canfly.append(iok)
         
    #     if lst_canfly:
    #         for ikoma in lst_canfly:
    #             cells = ikoma.getOuterCells(shogi.Gyoku.pos)
    #             if cells and cells[0] in poslst:
    #                 poslst.remove(cells[0])

    #     UkeOpeList =[]
    #     for ipos in poslst:
    #         UkeOpeList.append(Shogi_Operation(snd,False,shogi.Gyoku.char,False,shogi.Gyoku.pos,ipos))

    #     #print('__searchNigeUke',UkeOpeList)
    #     return UkeOpeList        

    # def __searchToriUke(self,shogi):
    #     UkeOpeList =[]
    #     xg,yg=shogi.Gyoku.pos
    #     otekomalst = shogi.ban[xg][yg].rch[fst]
    #     if len(otekomalst)>1:  #両王手で、同玉で大丈夫な場合
    #         for otekoma in otekomalst:
    #             xo,yo = otekoma.pos
    #             if otekoma.pos in shogi.Gyoku.rch and not shogi.ban[xo][yo].rch[fst]:
    #                 UkeOpeList.append(Shogi_Operation(snd,False,shogi.Gyoku.char,False,shogi.Gyoku.pos,otekoma.pos))
    #     elif len(otekomalst)==1:  #ダブル王手のときは、同玉以外に駒を取る受けはない。
    #         #print('王手している駒'+ str(otekomalst[0].pos)+ otekomalst[0].char)
    #         xc,yc=otekomalst[0].pos
    #         komaCandlst = shogi.ban[xc][yc].rch[snd]
    #         for icand in komaCandlst:
    #             #print('王手駒をとる', icand.char, icand.pos,[xc,yc])
    #             if icand == shogi.Gyoku:
    #                 if shogi.ban[xc][yc].rch[fst]:
    #                     continue       #攻め方の効きがある場合は同玉できない。
    #             #飛車角香の王手の道を開けてしまう場合を考慮する必要あり
    #             if self.__isBlocking(shogi,icand):
    #                 continue
    #             UkeOpeList.append(Shogi_Operation(snd,False,icand.char,False,icand.pos,otekomalst[0].pos))
    #             if icand.pchar and not icand.ispromoted:
    #                 if icand.pos[1]>5 or otekomalst[0].pos[1]>5:
    #                     UkeOpeList.append(Shogi_Operation(snd,False,icand.char,True,icand.pos,otekomalst[0].pos))

    #     #print('__searchToriUke',UkeOpeList)
    #     return UkeOpeList

    # def __searchAigoma(self,shogi):
        # idoUkeOpeList=[]
        # UkeOpeList =[]

        # xg,yg=shogi.Gyoku.pos
        # otekomalst = shogi.ban[xg][yg].rch[fst]


        # if len(otekomalst)!=1:  #ダブル王手のときは間駒はできない
        #     return [],[]
        
        # if not otekomalst[0].canFly:
        #     return [],[]
        
        # mudaAiCandsSet = []
        # cells =otekomalst[0].getInnerCells(shogi.Gyoku.pos)
        # mkomaCands = shogi.kdai[snd].keys()
        # for cell in cells:
        #     mudaAiCands = []
        #     x,y=cell
        #     rchfst=shogi.ban[x][y].rch[fst].copy() #cellに効きを持つ先手駒オブジェクトのリスト
        #     rchsnd=shogi.ban[x][y].rch[snd].copy() #cellに効きを持つ後手駒オブジェクトのリスト
        #     for i in rchsnd.copy(): #あらかじめ後手効き駒リストからPinされている駒を削除しておく。
        #         if self.__isBlocking(shogi,i):
        #             rchsnd.remove(i)

        #     #このセルに打てる合い駒リスト
        #     char_cands = []
        #     for mkoma in mkomaCands:
        #         if shogi.kdai[snd][mkoma]:
        #             if mkoma =='歩' and shogi.FuDic[snd][cell[0]]:
        #                 continue
        #             else:
        #                 char_cands.append(mkoma)
            
        #     numof_kiki = len(rchsnd)

        #     if numof_kiki == 0:
        #         for mkoma in char_cands:
        #             mudaAiCands.append(Shogi_Operation(snd,True,mkoma,False,None,cell))
        #     elif numof_kiki == 1:
        #         kikikoma = rchsnd[0]
        #         if kikikoma == shogi.Gyoku and  len(rchfst)>=2: #無駄合い候補手、合いゴマ効かずかどうかは__VerifyOuteCandidateメソッドに任せる。
        #             for mkoma in char_cands:
        #                 mudaAiCands.append(Shogi_Operation(snd,True,mkoma,False,None,cell))
        #         else:
        #             for mkoma in char_cands:
        #                 UkeOpeList.append(Shogi_Operation(snd,True,mkoma,False,None,cell))
        #             if kikikoma != shogi.Gyoku:
        #                 mudaAiCands.append(Shogi_Operation(snd,False,kikikoma.char,False,kikikoma.pos,cell))
        #                 if kikikoma.pos[1]>5 or cell[1]>5: #成って移動合い
        #                     mudaAiCands.append(Shogi_Operation(snd,False,kikikoma.char,True,kikikoma.pos,cell))

        #     else: #玉方の効きは２つ以上あるとき、移動合いは正当手
        #         for koma in rchsnd:
        #             if koma != shogi.Gyoku:
        #                 idoUkeOpeList.append(Shogi_Operation(snd,False,koma.char,False,koma.pos,cell))
        #                 if koma.pos[1]>5 or cell[1]>5: #成って移動合い
        #                     idoUkeOpeList.append(Shogi_Operation(snd,False,koma.char,True,koma.pos,cell))
        #         for mkoma in char_cands:
        #             UkeOpeList.append(Shogi_Operation(snd,True,mkoma,False,None,cell))

        #     if mudaAiCands:
        #         mudaAiCandsSet.append([cell,mudaAiCands])

        # return UkeOpeList+idoUkeOpeList,mudaAiCandsSet
 