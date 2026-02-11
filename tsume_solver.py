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

class TsumeSolver:
    
    def __init__(self):     #ver1.2修正でコンストラクタ化、ChuAiEnableを追加
        self.MaxStep=1
        self.dictop={}
        self.TotalCnt=0
        self.progress=True
        self.ChuAiEnable=False
    
    def Solve(self,shogi,MaxStep):
        self.dictop={}
        self.MaxStep=MaxStep
        self.TotalCnt=0
        count=0
        fisrtCands = self.searchOute(count,shogi)
        fisrtCands2 = self.__changeOrder(count,fisrtCands,shogi)
    
        if self.progress:
            print('初手候補',len(fisrtCands),':',fisrtCands)
    
        for iCand in fisrtCands2:
            dic={}
            ret=self.__VerifyOuteCandidate(count,shogi,iCand,dic)
            if self.progress:
                print('  ',iCand,'検証結果：',ret,'count',self.TotalCnt)
            if ret:     #ひとつ成功を見つけたらループ終了
                #print(DBG,'SolverTop2', iCand,'success, dic=',dic)
                self.dictop['next']=[iCand]
                self.dictop[iCand]=dic
                break
        return

    def __VerifyOuteCandidate(self,count,shogi,Cand,dict):
        count += 1
        self.TotalCnt += 1
        #dic['cnt']=count
        shogitmp=shogi.copy()
        shogitmp.DoOperation(Cand)
        #dic['next']=self.__SearchCandidates(count,shogitmp)
        ukeCands = self.searchUke(count,shogitmp)
        if self.progress and count==1:
            print('  ',Cand,'受け候補手',len(ukeCands),':',ukeCands)
        if ukeCands==[]:
            if Cand.char=='歩' and Cand.isUchi:
                return False    #打ち歩詰めは失敗
            dict['cnt']=count
            dict['next']=ukeCands
            dict['success']=True     #詰んだ
            #print(DBG,'  __VerifyOuteCandidate', Cand,'success')
            return True
        elif count == self.MaxStep: #手数になったが詰まなかった→MaxStepの次の受け手があったとき
            return False
       
        #王手候補手Candに対して、すべての受け候補ukaCnadを検証する。すべての受けが失敗すればCandは成功、ひとつでもukeCandが成功すればCandは失敗
        outeRes=True
        localdic1={}
        count += 1
        for ukeCand in ukeCands:
            localdic1[ukeCand]={}
            #ret = self.__VerifyCandidate(count,shogitmp,iCand,dic[iCand])
            self.TotalCnt += 1
            shogitmp2=shogitmp.copy()
            shogitmp2.DoOperation(ukeCand)
            nouteCands=self.searchOute(count,shogitmp2)
            if nouteCands==[]: #次に王手できないとき
                outeRes=False
                break   #この受けが成功で、成功する受けが存在するとき元の王手は失敗。

            #ukeCandに対するすべての次王手nxCandを検証する。すべてのnxCandが失敗すればukeCandは成功となる。ひとつでもnxCandが成功すればukeCandは失敗
            ukeRes=True
            retdic={}
            nouteCands2 = self.__changeOrder(count,nouteCands,shogitmp2)    #受け手数が少ない順番に入れ替える
            for nxCand in nouteCands2:
                oret = self.__VerifyOuteCandidate(count,shogitmp2,nxCand,retdic)
                if oret:     #ひとつでも王手が成功したら、この受けは失敗：
                    localdic1[ukeCand][nxCand] = retdic
                    localdic1[ukeCand]['cnt']=count
                    localdic1[ukeCand]['next']=[nxCand]
                    localdic1[ukeCand]['success']=False

                    #print(DBG,'__VerifyOuteCandidate2 nxCand',nxCand, 'success')
                    ukeRes=False #ukeCand失敗
                    break
            
            if ukeRes: #nxCandがすべて失敗したら
                outeRes=False
                break
        
        if outeRes: #ukeCandが全て失敗したら
            #print(DBG,'__VerifyOuteCandidate if outreslocaldic1=', localdic1)
            #dict = dict | localdic1
            dict['cnt']=count-1
            dict['success']=True
            dict['next']=ukeCands
            dict.update(localdic1)
            return True
        else:
            return False

    def __changeOrder(self,count,cands,shogi):
        if count>=self.MaxStep-1:
            return cands
        
        count+=1
        pair_cands=[]
        for icand in cands:
            shgtmp=shogi.copy()
            shgtmp.DoOperation(icand)
            ukecands=self.searchUke(count,shgtmp)
            
            pair_cands.append([icand,len(ukecands)])
        
        items_sorted = sorted(pair_cands, key=itemgetter(1))

        retcands=[]
        for i in items_sorted:
            retcands.append(i[0])

        return retcands

    def searchOute(self,count,shogi):

        lst_moveOute = self.__searchMoveOute(count,shogi)
        lst_uchiOute = self.__searchUchiOute(count,shogi)
        lst_HirakiOute = self.__searchHirakiOute(count,shogi)
        
        for h in lst_HirakiOute.copy():
            for m in lst_moveOute:
                if h.char==m.char and h.isUchi==m.isUchi and h.isNari==m.isNari and h.toPos==m.toPos and h.fromPos==m.fromPos:
                    lst_HirakiOute.remove(h)

        retlst = lst_uchiOute+lst_moveOute+lst_HirakiOute

        self.dbgprint('__searchOute'+str(retlst))
        return retlst
    
    def __searchMoveOute(self,count,shogi):
        OuteList = []
        for ikoma in shogi.kban[fst]:
            rchlst = ikoma.rch
            rchlst = ListOperator.subList(rchlst,shogi.distrib[fst])
            chkposlst = shogi.Gyoku.gen_chkposlst(ikoma.char,shogi.distrib[mix])
            chklst = ListOperator.andList(rchlst,chkposlst)
            self.dbgprint('__searchMoveOute'+ikoma.char+str(chklst))

            #成王手を先にする
            if ikoma.pchar and not ikoma.ispromoted:
                chkposlst = shogi.Gyoku.gen_chkposlst(ikoma.pchar,shogi.distrib[mix])
                chkposlst = ListOperator.subList(chkposlst,shogi.distrib[fst])
                chklst2 = ListOperator.andList(rchlst,chkposlst)
            
                for ipos in chklst2:
                    if ikoma.pos[1]<3 or ipos[1]<3:
                        OuteList.append(Shogi_Operation(fst,False,ikoma.char,True,ikoma.pos,ipos))

            for ipos in chklst:
                if ipos == shogi.Gyoku.pos:
                    print('error')
                OuteList.append(Shogi_Operation(fst,False,ikoma.char,False,ikoma.pos,ipos))

        self.dbgprint('__searchMoveOute'+str(OuteList))
        return OuteList
    
    def __searchUchiOute(self,count,Shogi):
        OuteList = []
        for ichar in Shogi.kdai[fst].keys():
                if Shogi.kdai[fst][ichar]:
                    if ichar == '歩' and Shogi.FuDic[fst][Shogi.Gyoku.pos[0]]:
                        continue   #二歩防止のため、候補手に入れない。打ち歩詰め防止は__VerifyOuteCandidateの詰み判定にて実施
                    chkposlst=Shogi.Gyoku.gen_chkposlst(ichar,Shogi.distrib[mix])
                    chkposlst=ListOperator.subList(chkposlst,Shogi.distrib[mix])
                    for ipos in chkposlst:
                        OuteList.append(Shogi_Operation(fst,True,ichar,False,None,ipos))
        self.dbgprint('__searchUchiOute'+str(OuteList))

        return OuteList
    
    def __searchHirakiOute(self,count,Shogi):
        OuteList = []
        for ikoma in Shogi.kban[fst]:
            flyer = self.__isBlocking(Shogi,ikoma)
            if flyer:
                waycells=flyer.getInnerCells(ikoma.pos)+flyer.getOuterCells(ikoma.pos)
                cells = ListOperator.subList(ikoma.rch,waycells+Shogi.distrib[fst])
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

    def searchUke(self,count,shogi):
        lst_Tori = self.__searchToriUke(count,shogi)
        lst_Nige = self.__searchNigeUke(count,shogi)
        lst_aigoma = self.__searchAigoma(count,shogi)
    
        self.dbgprint('__searchUke'+str(lst_Nige+lst_Tori+lst_aigoma))
        return lst_Tori+lst_Nige+lst_aigoma

    def __searchNigeUke(self,count,shogi):
        xg,yg=shogi.Gyoku.pos
        outeKomaLst = shogi.ban[xg][yg].rch[fst]
        outeKomaPosLst=[]
        for ikoma in outeKomaLst:
            outeKomaPosLst.append(ikoma.pos)
        
        poslst = []
        for ipos in shogi.Gyoku.rch:
            x,y= ipos
            if (shogi.ban[x][y].rch[fst]==[]) and not (ipos in shogi.distrib[snd]): #相手の効きがなく、味方のいないところ
                if ipos not in outeKomaPosLst:  #同玉はToriukeで考慮済み。
                    poslst.append(ipos)
        #print('Solver:__searchNigeUke  poslst=',poslst)
        
        #飛車角香の効き延長を考慮、移動先が効きの延長線上であれば、この移動先はリストposlstから削除する。
        xg,yg=shogi.Gyoku.pos
        okomalst = shogi.ban[xg][yg].rch[fst]
        lst_canfly=[]
        for iok in okomalst:
            if iok.canFly:
                lst_canfly.append(iok)
         
        if lst_canfly:
            for ikoma in lst_canfly:
                cells = ikoma.getOuterCells(shogi.Gyoku.pos)
                if cells and cells[0] in poslst:
                    poslst.remove(cells[0])

        UkeOpeList =[]
        for ipos in poslst:
            UkeOpeList.append(Shogi_Operation(snd,False,shogi.Gyoku.char,False,shogi.Gyoku.pos,ipos))

        #print('__searchNigeUke',UkeOpeList)
        return UkeOpeList        

    def __searchToriUke(self,count,shogi):
        UkeOpeList =[]
        xg,yg=shogi.Gyoku.pos
        otekomalst = shogi.ban[xg][yg].rch[fst]
        if len(otekomalst)>1:  #両王手で、同玉で大丈夫な場合
            for otekoma in otekomalst:
                xo,yo = otekoma.pos
                if otekoma.pos in shogi.Gyoku.rch and not shogi.ban[xo][yo].rch[fst]:
                    UkeOpeList.append(Shogi_Operation(snd,False,shogi.Gyoku.char,False,shogi.Gyoku.pos,otekoma.pos))
        elif len(otekomalst)==1:  #ダブル王手のときは、同玉以外に駒を取る受けはない。
            #print('王手している駒'+ str(otekomalst[0].pos)+ otekomalst[0].char)
            xc,yc=otekomalst[0].pos
            komaCandlst = shogi.ban[xc][yc].rch[snd]
            for icand in komaCandlst:
                #print('王手駒をとる', icand.char, icand.pos,[xc,yc])
                if icand == shogi.Gyoku:
                    if shogi.ban[xc][yc].rch[fst]:
                        continue       #攻め方の効きがある場合は同玉できない。
                #飛車角香の王手の道を開けてしまう場合を考慮する必要あり
                if self.__isBlocking(shogi,icand):
                    continue
                UkeOpeList.append(Shogi_Operation(snd,False,icand.char,False,icand.pos,otekomalst[0].pos))
                if icand.pchar and not icand.ispromoted:
                    if icand.pos[1]>5 or otekomalst[0].pos[1]>5:
                        UkeOpeList.append(Shogi_Operation(snd,False,icand.char,True,icand.pos,otekomalst[0].pos))

        #print('__searchToriUke',UkeOpeList)
        return UkeOpeList

    def __searchAigoma(self,count,shogi):
        idoUkeOpeList=[]
        UkeOpeList =[]
        poslist=[]
        xg,yg=shogi.Gyoku.pos
        otekomalst = shogi.ban[xg][yg].rch[fst]
        if len(otekomalst)==1:  #ダブル王手のときは間駒はできない
            #print('王手している駒'+ str(otekomalst[0].pos)+ otekomalst[0].char)
            if otekomalst[0].canFly:
                cells =otekomalst[0].getInnerCells(shogi.Gyoku.pos)
                for cell in cells:
                    x,y=cell
                    rchfst=shogi.ban[x][y].rch[fst]
                    rchsnd=shogi.ban[x][y].rch[snd]
                    for i in rchsnd.copy(): #あらかじめ後手効き駒リストからPinされている駒を削除しておく。
                        if self.__isBlocking(shogi,i):
                            rchsnd.remove(i)

                    for i in rchsnd:
                        if i==shogi.Gyoku and len(rchsnd)==1 and len(rchfst)>1: #王手している駒の他に先手の効きがあるとき
                            continue    #間駒効かず
                        else:
                            if i!=shogi.Gyoku:
                                idoUkeOpeList.append(Shogi_Operation(snd,False,i.char,False,i.pos,cell))   #移動合い
                                if i.pchar and not i.ispromoted:
                                    if i.pos[1]>5 or cell[1]>5:
                                        idoUkeOpeList.append(Shogi_Operation(snd,False,i.char,True,i.pos,cell))    #移動合い、成り
                            if cell not in poslist: #echsndに複数利き駒があるときに　複数の同一候補手が発生してしまう不具合の修正　2025/12/20
                                poslist.append(cell)    #合い駒打ちポイントのリストに追加

                    if cell not in poslist:
                        for i in rchfst:    #先手の飛車角香の焦点への間駒
                            if i.canFly:
                                if otekomalst[0].char=='飛' or otekomalst[0].char=='龍':
                                    if i.char=='角' or i.char=='馬':
                                        if self.__isFocus(shogi,cell,i,otekomalst[0]):
                                            poslist.append(cell)
                                elif otekomalst[0].char=='香':
                                    if i.char=='飛' or i.char=='龍' or i.char=='角' or i.char=='馬':
                                        if self.__isFocus(shogi,cell,i,otekomalst[0]):
                                            poslist.append(cell)
                                elif otekomalst[0].char=='角' or otekomalst[0].char=='馬':
                                    if i.char=='香' or i.char=='飛' or i.char=='龍':
                                        if self.__isFocus(shogi,cell,i,otekomalst[0]):
                                            poslist.append(cell)

                if self.ChuAiEnable:    #玉の2つ手前に中合いする。ver1.2修正
                    if len(cells)>1:
                        if not cells[-2] in poslist:
                            poslist.append(cells[-2])

                mkomaCands = shogi.kdai[snd].keys()
                for cell in poslist:
                    for mkoma in mkomaCands:
                                if shogi.kdai[snd][mkoma]:
                                    if mkoma =='歩' and shogi.FuDic[snd][cell[0]]: #二歩の合い駒を防止
                                        continue
                                    UkeOpeList.append(Shogi_Operation(snd,True,mkoma,False,None,cell))

        return UkeOpeList+idoUkeOpeList
    
    def __isFocus(self,shogi,cell,flyer,otekoma):
        outercells = flyer.getOuterCells(cell)
        if outercells:
            x,y=outercells[0]
            if shogi.ban[x][y].isOpen():
                tmpshg=shogi.copy()
                tmpshg.DoOperation(Shogi_Operation(fst,False,otekoma.char,False,otekoma.pos,cell))
                cands=self.__searchNigeUke(0,tmpshg)
                cands+=self.__searchToriUke(0,tmpshg)
                if cands:
                    return True
        return False
    
    def __isBlocking(self,shogi,koma):
        return shogi.isBlocking(koma)

    def dbgprint(self,txt):
        # print(txt)
        pass

    def HierPrintDic(self,fp):
        if self.dictop == {}:
            print('could not find sokution in ',self.MaxStep,'steps')
            print('Please check original problem or steps')
            return
        print('****Solution****')
        count=1
        dic = self.dictop
        next=dic['next']
        for i_ope in next:
            if i_ope in dic.keys():
                print('  *',dic[i_ope]['cnt'],i_ope,dic[i_ope]['success'])
                if autoTestMode:
                    print('  *',dic[i_ope]['cnt'],i_ope,dic[i_ope]['success'], file=fp)
                self.__subHierPrintDic(dic[i_ope],count,fp)
            
        return
    
    def __subHierPrintDic(self,dic,count,fp):

        count+=1
        if count>self.MaxStep:
            return
        
        next=dic['next']
        for i_ope in next:
            if i_ope in dic:
                print('    '*count,dic[i_ope]['cnt'],i_ope,dic[i_ope]['success'])
                if autoTestMode:
                    print('    '*count,dic[i_ope]['cnt'],i_ope,dic[i_ope]['success'],file=fp)
                self.__subHierPrintDic(dic[i_ope],count,fp)

        return

    def GetSolution(self):
        if self.dictop == {}:
            print('could not find sokution in ',self.MaxStep,'steps')
            print('Please check original problem or steps')
            return False

        lst_sol=[]
        dic=self.dictop
        count=1
        next=dic['next']


        #最初にdic階層のdepthを求める
        self.depth=0
        for i_ope in next:
            self.__subSearchDepth(dic[i_ope])
            
        print('GetSolution__subSerachDepth depth=',self.depth)

        for i_ope in next:
            if i_ope in dic.keys():
                print('  *',dic[i_ope]['cnt'],i_ope,dic[i_ope]['success'])
                ret = self.__subGetSolution(dic[i_ope],count,lst_sol)
                if ret or self.depth==1:
                    lst_sol.append(i_ope)
        
        lst_sol.reverse()
        
        return lst_sol

    def __subSearchDepth(self,dic):
        if dic['cnt']>self.depth:
            self.depth=dic['cnt']

        for i_ope in dic['next']:
            self.__subSearchDepth(dic[i_ope])

    def __subGetSolution(self,dic,count,lst_sol):

        count+=1
        if count>self.MaxStep:
            return False
        
        next=dic['next']
        for i_ope in next:
            if i_ope in dic:
                print('    '*count,dic[i_ope]['cnt'],i_ope,dic[i_ope]['success'])
                if dic[i_ope]['cnt']==self.depth and dic[i_ope]['success']==True:
                    lst_sol.append(i_ope)
                    return True
                ret=self.__subGetSolution(dic[i_ope],count,lst_sol)
                if ret:
                    lst_sol.append(i_ope)
                    return True

        return False
