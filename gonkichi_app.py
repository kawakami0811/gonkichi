#Gonkichi アプリ 2026.6 Slover2mdsc、中合いフラグ削除、中合い候補手表示(Gameモード）、cython対応
import time
import tkinter
import pickle
import datetime
from tkinter import END
from tkinter import filedialog
from tkinter import messagebox
import tkinter.messagebox
from PIL import Image, ImageTk
import base64,io

try:
    from shogi_cy import fst,snd,Shogi
    print("⚡⚡Using Shogi from shogi_cy.pyd")
except:
    from shogi import fst,snd,Shogi
    print("■Using Shogi from shogi.py")

from resource_base64 import dic_base64,icon_base64,koma_base64
from tsume_solver2mdsc import TsumeSolver2mdsc


class koma_select:
    koma=None   #komaオブジェクト指定
    char=''     #駒文字
    ix,iy=0,0   #座標
    owner=''    #先手(fst)/後手(snd)
    canvas=None #盤または駒台のCanvasオブジェクト
    pdaifst,pdaisnd,pban='dai_fst','dai_snd','ban'
    place =''   #版または駒台の区別　↑で定義
    
class TsumeShogi:
    def __init__(self,shogi,n):
        self.shogi=Shogi()
        shogi.copyto(self.shogi)
        self.n_tedume = n
        self.hint=''
        self.answer=[]
        return

    def makeSolution(self,lst):
        self.answer.append(self.shogi)
        for i in range(self.n_tedume):
            shg=Shogi()
            self.answer[i].copyto(shg)
            shg.DoOperation(lst[i])
            self.answer.append(shg)
        return

# ステイタスの親クラス       
class GAppState:
    def __init__(self):
        pass
    
    def onClickBan(self,app,event):
        raise NotImplementedError("You should implement this method!!")
    
    def onRightClickBan(self,app,event):
        raise NotImplementedError("You should implement this method!!")
    
    def onDblClickBan(self,app,event):
        raise NotImplementedError("You should implement this method!!")

    def onClickFstKdai(self,app,event):
        raise NotImplementedError("You should implement this method!!")

    def onClickSndKdai(self,app,event):
        raise NotImplementedError("You should implement this method!!")

# 駒ならべステイタス
class StateArrange(GAppState):
    def onClickBan(self,app,event):
        app.onClickBan_arr(event)
    
    def onRightClickBan(self,app,event):
        app.onRightClickBan_arr(event)
    
    def onDblClickBan(self,app,event):
        app.onDblClickBan_arr(event)

    def onClickFstKdai(self,app,event):
        app.onClickFstKdai_arr(event)

    def onClickSndKdai(self,app,event):
        app.onClickSndKdai_arr(event)

# 将棋ゲームステイタス
class StateGame(GAppState):
    def onClickBan(self,app,event):
        #print("Gamemode")
        app.onClickBan_game(event)
    
    def onRightClickBan(self,app,event):
        pass    #何もしない
    
    def onDblClickBan(self,app,event):
        pass    #何もしない

    def onClickFstKdai(self,app,event):
        print("Gamemode")
        app.onClickFstKdai_game(event)

    def onClickSndKdai(self,app,event):
        print("Gamemode")
        app.onClickSndKdai_game(event)

# 詰将棋アプリ「言吉」本体
class GonkichiApp:

    wm=60   #一マスの幅　縦横同じ（正方形）
    we=30   #列番号表示の幅
    ofst=2
    sfx_dan=['一','ニ','三','四','五','六','七','八','九']
    imgkeys=['金','銀','桂','香','歩','飛','角','玉','全','圭','杏','と','龍','馬']
    colkoma='#E6AA5A'
    colboard='#BE7832'
    colormat='#96CB96'
    sts_waiting,sts_selected = 'waiting','selected'


    def __init__(self):
        self.shogi=None
        self.tsumeshg=None
        self.i_step=0
        # self.solver=TsumeSolver()
        self.solver2 = TsumeSolver2mdsc() #新Solver
        # self.solver3 = TsumeSolver3() #IDDFS solver
        self.selection=koma_select()
        self.id_selmark=None
        self.imgMarker=None
        self.imgFromMarker=None
        self.imgToMarker=None
        self.curState= self.sts_waiting     #駒を動かすときの状態。初期状態は動かす駒の選択待ち状態。（cf 選択済み・移動先選択状態）
        self.lstIdBan=[]
        self.dicIdDai = {fst:[],snd:[]}
        self.dic_kimg={fst:{},snd:{}}
        self.gameState = StateArrange()     #駒を動かすモードの選択。初期状態はアレンジモード（cf ゲームモード）
        self.cand={True:[],False:[]}    #True:駒台から打つ、False：盤上の駒移動
        self.dicIdMarker = {}
        self.dicCanv={}
        self.koma = {}

    def setup(self):
        self.setup_window()
        self.setupDicIdMarker()
        self.setup_komaimg()
        self.setup_shogi()
        self.refreshDispBan()
        self.refreshDispDai()
        self.showWindow()

    def setup_shogi(self):
        self.shogi=Shogi()
        self.shogi.gen_komas()
        #self.shogi.D36_9_test()
        self.tsumeshg=TsumeShogi(self.shogi,1)

    def refreshDispBan(self):
        while self.lstIdBan:
            self.canvas_ban.delete(self.lstIdBan.pop())
    
        for owr in self.shogi.kban:
            for ikoma in self.shogi.kban[owr]:
                ix,iy=ikoma.pos
                self.drawKomaBan(ix,iy,owr,ikoma.char)
        
        #利きの表示
        gameMode = self.GameMode.get()
        rchfst = self.rchFst.get()
        rchsnd = self.rchSnd.get()
        
        if not gameMode or not any([rchfst,rchsnd]): #GameModeでない場合と、GameModeであっても▲▽チェックなしのときはなここで終了
            return
        
        for ix in range(9):
            for iy in range(9):
                if rchfst and self.shogi.ban[ix][iy].rch[fst]:
                    self.drawRchBan(ix,iy,self.imgRchFst)
                if rchsnd and self.shogi.ban[ix][iy].rch[snd]:
                    self.drawRchBan(ix,iy,self.imgRchSnd)
        
        #self.drawKomaBan(8,0,snd,'金')
        #self.drawKomaBan(4,4,fst,'龍')
        return

    def refreshDispDai(self):
        for owr,cv in [[fst,self.canvas_fst],[snd, self.canvas_snd]]:
            while self.dicIdDai[owr]:
                cv.delete(self.dicIdDai[owr].pop())

            self.drawKomaDai(cv,self.shogi.kdai,owr)

    def drawRchBan(self,ix,iy,img):
        x,y=self.__Index2Coordinates(ix,iy)
        self.lstIdBan.append(self.canvas_ban.create_image(x,y,image=img))   #利きマーカーも駒と同じIDリストを使う。

    def drawKomaBan(self,ix,iy,owner,char):
        x,y=self.__Index2Coordinates(ix,iy)
        if owner==fst:
            # id_pol=self.canvas_ban.create_polygon(x,y-25,x-20,y-20,x-25,y+25,x+25,y+25,x+20,y-20,width=2,fill=self.colkoma,outline='black')
            id_pol = self.canvas_ban.create_image(x,y,image=self.koma[fst])
        else:
            # id_pol=self.canvas_ban.create_polygon(x,y+25,x-20,y+20,x-25,y-25,x+25,y-25,x+20,y+20,width=2,fill=self.colkoma,outline='black')
            id_pol = self.canvas_ban.create_image(x,y,image=self.koma[snd])
        self.lstIdBan.append(id_pol)
        
        self.lstIdBan.append(self.canvas_ban.create_image(x,y,image=self.dic_kimg[owner][char]))

    def drawKomaDai(self,canvas,kdai,owr):
        x=60
        y=60
        for char in kdai[owr]:
            if kdai[owr][char]:
                self.dicIdDai[owr].append(canvas.create_image(x,y,image=self.koma[owr]))
                self.dicIdDai[owr].append(canvas.create_image(x,y,image=self.dic_kimg[owr][char]))
                self.dicIdDai[owr].append(canvas.create_text(x+60,y,font=('',24),text=str(len(kdai[owr][char]))))
            y+=self.wm
        return

    def __Index2Coordinates(self,ix,iy):
        x=self.wm*ix + self.wm//2
        y=self.wm*iy + self.wm//2 +self.we
        return x,y

    def __Coordinates2Index(self,ex,ey):
        ix = ex//self.wm
        iy = (ey-self.we)//self.wm
        return ix,iy

    def setup_komaimg(self):

        for char in self.imgkeys:
            b64 = dic_base64[char]
            binary = base64.b64decode(b64)
            image = Image.open(io.BytesIO(binary))
            rotateImage = image.rotate(180,expand=1)

            self.dic_kimg[fst][char]=ImageTk.PhotoImage(image)
            self.dic_kimg[snd][char]=ImageTk.PhotoImage(rotateImage)

        #駒画像（文字なし）
        koma_bin = base64.b64decode(koma_base64)
        koma_img = Image.open(io.BytesIO(koma_bin))
        rotate_koma_img = koma_img.rotate(180,expand=1)
        self.koma[fst]=ImageTk.PhotoImage(koma_img)
        self.koma[snd]=ImageTk.PhotoImage(rotate_koma_img)
        
        image= Image.new("RGBA", (60, 60), (230, 120, 120, 128))
        self.imgMarker=ImageTk.PhotoImage(image)
        
        image= Image.new("RGBA", (60, 60), (120, 230, 230, 128))    #Gameモードの駒選択カーソル
        self.imgFromMarker=ImageTk.PhotoImage(image)
        image= Image.new("RGBA", (60, 60), (230, 120, 230, 128))    #Gameモードの行き先選択カーソル
        self.imgToMarker=ImageTk.PhotoImage(image)
        
        image= Image.new("RGBA", (60, 60), (0, 0, 170, 128))
        self.imgRchFst = ImageTk.PhotoImage(image)
        image= Image.new("RGBA", (60, 60), (200, 0, 0, 128))
        self.imgRchSnd = ImageTk.PhotoImage(image)

    def setup_window(self):
        self.root=tkinter.Tk()
        self.root.title('Gonkichi Solver')
        icon_image_data = base64.b64decode(icon_base64)
        icon_image = Image.open(io.BytesIO(icon_image_data))
        icon = ImageTk.PhotoImage(icon_image)
        self.root.wm_iconphoto(True,icon)
        # self.root.iconbitmap('gonkichi_zero/Gonkichi.ico')
        self.root.geometry('1000x750')
        
        FONT = ('Arial',10,'bold')

        #Menuバー　Fileメニュー
        self.menubar = tkinter.Menu(self.root)
        self.filemanu = tkinter.Menu(self.menubar)
        self.filemanu.add_command(label='Load', command=self.ldbtn_pushed)
        self.filemanu.add_command(label='Save',command=self.svbtn_pushed)
        self.filemanu.add_separator()
        self.filemanu.add_command(label='Exit',command=self.root.quit)
        self.menubar.add_cascade(label='File', menu=self.filemanu)
        self.root.config(menu=self.menubar)

        #Solverフレーム frame_slvr5
        frame_slvr = tkinter.Frame(self.root)
        frame_slvr.pack()
        
        self.ent_n=tkinter.Entry(frame_slvr, width=2,font=FONT)
        self.ent_n.insert(0,5)
        self.ent_n.grid(row=0,column=0)
        label_n= tkinter.Label(frame_slvr, text='手詰め',font=FONT )
        label_n.grid(row=0,column=1)
        self.btn_slv = tkinter.Button(frame_slvr, text='Solve' , command = self.slvbtn_pushed, font=FONT, bg='pink')
        self.btn_slv.grid(row=0,column=2,padx=10)


        self.btn_init=tkinter.Button(frame_slvr,text='◀◀', command = self.initbtn_pushed, font=FONT, bg='gray',state=tkinter.DISABLED)
        self.btn_init.grid(row=0,column=3,padx=10)
        self.btn_bw=tkinter.Button(frame_slvr,text='◀', command = self.bwbtn_pushed, font=FONT, bg='gray',state=tkinter.DISABLED)
        self.btn_bw.grid(row=0,column=4,padx=10)
        self.btn_play=tkinter.Button(frame_slvr,text='▶', command = self.playbtn_pushed, font=FONT, bg='gray',state=tkinter.DISABLED)
        self.btn_play.grid(row=0,column=5,padx=10)
        self.btn_final=tkinter.Button(frame_slvr,text='▶▶', command = self.finalbtn_pushed, font=FONT, bg='gray',state=tkinter.DISABLED)
        self.btn_final.grid(row=0,column=6,padx=10)
        self.btn_clr=tkinter.Button(frame_slvr,text='Clear', command = self.clrbtn_pushed, font=FONT, bg='gray',state=tkinter.DISABLED)
        self.btn_clr.grid(row=0,column=7,padx=10)
        
        # self.chuai=tkinter.BooleanVar()
        # self.chuai.set(False)
        # self.chbx_Chuai=tkinter.Checkbutton(frame_slvr, variable=self.chuai,text='中合い', font=FONT, command= self.chbx_chuaiModeCallBack)
        # self.chbx_Chuai.grid(row=0,column=9,padx=20)
        
        self.GameMode=tkinter.BooleanVar()
        self.GameMode.set(False)
        self.chbx_Game=tkinter.Checkbutton(frame_slvr, variable=self.GameMode,text='GAME', font=FONT, command=self.chbx_gameModeCallBack)
        self.chbx_Game.grid(row=0,column=10,padx=20)

        self.rchFst=tkinter.BooleanVar()
        self.rchFst.set(False)
        self.chbx_rchFst = tkinter.Checkbutton(frame_slvr, variable=self.rchFst,text='▲',foreground='blue',font=('Arial',11,'bold'),command=self.refreshDispBan)
        self.chbx_rchFst.grid(row=0,column=11,padx=10)
        self.rchSnd=tkinter.BooleanVar()
        self.rchSnd.set(False)
        self.chbx_rchSnd = tkinter.Checkbutton(frame_slvr, variable=self.rchSnd,text='▽',foreground='red', font=('Arial',11,'bold'),command=self.refreshDispBan)
        self.chbx_rchSnd.grid(row=0,column=12,padx=10)

        #メッセージフレーム　frame_msg
        frame_msg = tkinter.Frame(self.root)
        frame_msg.pack()
        self.label_msg= tkinter.Label(frame_msg, text='arrange, set number , then push [Solve]',font=FONT )
        self.label_msg.grid(row=0,column=0)

        #将棋盤と駒台のCanvas
        frame_boad = tkinter.Frame(self.root, width=720+self.we,height=540+self.we,bg='white')
        frame_boad.pack()
        self.canvas_ban= tkinter.Canvas(frame_boad, width=540+self.we+self.ofst,height=540+self.we,background=self.colboard)
        
        self.drawMasu()
        
        self.canvas_ban.grid(row=0,column=1)
        self.canvas_ban.bind("<Button-1>",self.onClikcBan)
        self.canvas_ban.bind("<Button-3>",self.onRightClickBan,add=True)
        self.canvas_ban.bind("<Double-1>",self.onDblClickBan,add=True)

        self.canvas_fst=tkinter.Canvas(frame_boad,width=180,height=540,background=self.colormat)
        self.canvas_fst.bind("<Button-1>",self.onClickFstKdai)
        self.canvas_fst.grid(row=0,column=2)

        self.canvas_snd=tkinter.Canvas(frame_boad,width=180,height=540,background=self.colormat)
        self.canvas_snd.bind("<Button-1>",self.onClickSndKdai)
        self.canvas_snd.grid(row=0,column=0)

    def setupDicIdMarker(self):
        for icanvas in [self.canvas_ban,self.canvas_fst, self.canvas_snd]:
            self.dicIdMarker[icanvas]=[]
            
        self.dicCanv[fst]=self.canvas_fst
        self.dicCanv[snd]=self.canvas_snd

    def deleteAllMarkers(self):
        for icanvas in [self.canvas_ban,self.canvas_fst, self.canvas_snd]:
            idlst = self.dicIdMarker[icanvas]
            while idlst!=[]:
                icanvas.delete(idlst.pop())

    def chbx_gameModeCallBack(self):
        self.curState=self.sts_waiting
        self.deleteAllMarkers()
        self.selection=koma_select()

        if self.GameMode.get():
            self.gameState=StateGame()
            self.shogi.extend_reach_all()
            if not self.tsumeshg.answer:
                cpyshg = Shogi()
                self.shogi.copyto(cpyshg)
                self.tsumeshg.answer.append(cpyshg)
            #候補手の探索と表示

            self.searchDispCand()
        else:
            self.gameState = StateArrange()
            if tkinter.messagebox.askquestion(title='Question',message='手順をクリアしますか？')=='yes':
                self.clrbtn_pushed()

        self.refreshDispBan() #利き表示をリフレッシュする。

    def svbtn_pushed(self):
        filename = filedialog.asksaveasfilename(filetypes=[('Pickle files','*.pickle')],defaultextension='pickle')
        #print(DBG,'svbtn_pushed: file=',filename)
        cpyshg = Shogi()
        self.shogi.copyto(cpyshg)
        self.tsumeshg.shogi = cpyshg
        self.tsumeshg.n_tedume=int(self.ent_n.get())
        with open(filename,'wb') as file:
            pickle.dump(self.tsumeshg,file)
        file.close()

    def ldbtn_pushed(self):
        filepath = filedialog.askopenfilename(filetypes=[('Pickle files','*.pickle')])
        #print(DBG,'ldbtn_pushed: file=',filepath)
        with open (filepath,'rb') as file:
            self.tsumeshg=pickle.load(file)
        file.close()
        self.label_msg['text']='Load:'+filepath
        if self.tsumeshg.answer==[]:
            self.clrbtn_pushed()
            self.shogi=self.tsumeshg.shogi.copyto(Shogi())
            self.ent_n.delete(0,END)
            self.ent_n.insert(0,self.tsumeshg.n_tedume)
            self.refreshDispBan()
            self.refreshDispDai()
        else:
            self.ent_n.delete(0,END)
            self.ent_n.insert(0,self.tsumeshg.n_tedume)
            self.enableButton(self.btn_clr)
            self.i_step=0
            self.showSteps()
        
        return

    def onRightClickBan(self,event):
        self.gameState.onRightClickBan(self,event)

    def onRightClickBan_arr(self,event):
        ix,iy = self.__Coordinates2Index(event.x,event.y)

        if ix<9 and iy<9:
            if self.curState==self.sts_waiting:
                koma= self.shogi.ban[ix][iy].get_koma()
                if koma and not koma.char=='玉':
                    self.shogi.change_owner_ban(ix,iy)
                    self.refreshDispBan()
        return
    
    def onDblClickBan(self,event):
        self.gameState.onDblClickBan(self,event)
    
    def onDblClickBan_arr(self,event):
        ix,iy = self.__Coordinates2Index(event.x,event.y)
        
        if ix<9 and iy<9:
            koma= self.shogi.ban[ix][iy].get_koma()
            if koma:
                if koma.ispromoted:
                    koma.reset()
                else:
                    koma.promote()
                self.refreshDispBan()
                self.onClikcBan(event)
        return

    def onClickFstKdai(self,event):
        self.gameState.onClickFstKdai(self,event)

    def onClickFstKdai_arr(self,event):
        self.onClickKdai_arr(event,fst)
        return

    def onClickFstKdai_game(self,event):
        self.onClickKdai_game(event,fst)
        pass

    def onClickSndKdai(self,event):
        self.gameState.onClickSndKdai(self,event)

    def onClickSndKdai_arr(self,event):
        self.onClickKdai_arr(event,snd)
        return

    def onClickSndKdai_game(self,event):
        self.onClickKdai_game(event,snd)
        pass

    def onClickKdai_arr(self,event,owner):
        if self.curState==self.sts_waiting:
            iy=(event.y-30)//self.wm
            if iy>=0 and iy<=6:
                lst_char = list(self.shogi.kdai[owner].keys())
                char=lst_char[iy]
                print('onClickKdai: owne,iy,char=',owner,iy,lst_char[iy])
                if self.shogi.kdai[owner][char]:
                    self.selection.char = char
                    if owner==fst:
                        self.selection.place=koma_select.pdaifst
                        self.selection.canvas=self.canvas_fst
                    else:
                        self.selection.place=koma_select.pdaisnd
                        self.selection.canvas=self.canvas_snd
                    self.selection.owner=owner
                    self.curState=self.sts_selected
                    self.dispSelMarkDai(self.selection.canvas,iy,self.imgMarker)
                else:
                    print('Enmty: not selected',char)
        elif self.curState==self.sts_selected:
            if self.selection.place==koma_select.pban:
                if not self.selection.koma.char == '玉':
                    self.shogi.ban2dai_koma(self.selection.koma,owner)
                    self.selectionDone()

            else:
                if not self.selection.owner==owner:
                    self.shogi.change_owner_kdai(self.selection.owner,owner,self.selection.char)
                    print('chang owner dai', self.selection.owner,'>',owner)
                self.selectionDone()
        return

    def onClickKdai_game(self,event,owner):
        if self.curState == self.sts_selected:  #駒選択済みのときは何もしない→セレクトをキャンセルしてやり直す。
            self.cancelSellection_game()
            return

        iy=(event.y-30)//self.wm
        if iy>=0 and iy<=6:
            lst_char = list(self.shogi.kdai[owner].keys())
            char=lst_char[iy]
            
            newlst=[]
            for icand in self.cand[True]:
                if icand.owner != owner:
                    return  #手番とクリックされたCanvasが一致しないときは何もしない。
                if icand.isUchi and icand.char==char:
                    newlst.append(icand)
            
            if newlst==[]:
                return
            else:
                self.deleteAllMarkers()

                self.cand[False]=[]     #移動の候補手は消す
                self.cand[True]=newlst
                for icand in newlst:
                    jx,jy=icand.toPos
                    self.dispSelMarkBan(jx,jy,self.imgToMarker)
                self.curState=self.sts_selected
                
                self.dispSelMarkDai(self.dicCanv[owner],iy,self.imgFromMarker)

    def cancelSellection_game(self):
        self.curState=self.sts_waiting
        self.deleteAllMarkers()
        self.chbx_gameModeCallBack()

    def selectionDone(self):
        self.curState=self.sts_waiting
        self.deleteAllMarkers()
        self.selection=koma_select()
        self.refreshDispBan()
        self.refreshDispDai()

        return

    def drawMasu(self):
        for ix in range(9):
            for iy in range(9):
                self.canvas_ban.create_rectangle(ix*self.wm+2,iy*self.wm+self.we+2,(ix+1)*self.wm,(iy+1)*self.wm+self.we,width=2)
                self.canvas_ban.create_text(ix*self.wm+self.wm//2,15+self.ofst,text=str(9-ix),fill='black',font=('',18,'bold'))
        for iy in range(9):
            self.canvas_ban.create_text(540+15+self.ofst,self.wm*iy+self.wm//2+self.we+self.ofst,text=self.sfx_dan[iy],fill='black',font=('',14))

    def showWindow(self):
        self.root.update()
        self.root.deiconify()
        self.root.mainloop()

    def slvbtn_pushed(self):
        self.label_msg['text']='Please wait. thinking...'
        self.shogi.extend_reach_all()
        n=int(self.ent_n.get())
        self.tsumeshg=TsumeShogi(self.shogi,n)
        #self.solver.ChuAiEnable = self.chuai.get()  #ver1.2 中合いEnableの値を取得してSolverにセットする。
    
        t_start=time.time()
        self.solver2.Solve_mdsc(self.shogi,n)
        t_end=time.time()
        t_calc=round(t_end-t_start,3)

        if self.solver2.dictop=={}:
            print('Failed to find solution')
            self.label_msg['text']='Failed to find solution! Please check and try again'
        else:
            self.solver2.HierPrintDic()
            lst_ope=self.solver2.GetSolution2()
            print('Solution found!',lst_ope)
            self.label_msg['text']='Found solution!  in '+str(t_calc)+'[sec]  TotalCount:'+str(self.solver2.TotalCnt)
            if len(lst_ope) < n:    #実際にはより短い手数で解けたとき
                self.tsumeshg.n_tedume=len(lst_ope)
                self.label_msg['text']='Solved in fewer steps'
                self.ent_n.delete(0,END)
                self.ent_n.insert(0,len(lst_ope))
            self.tsumeshg.makeSolution(lst_ope)
            self.i_step=0
            self.enableButton(self.btn_clr)
            self.showSteps()

    def clrbtn_pushed(self):
        self.i_step=0
        self.disableButton(self.btn_init)
        self.disableButton(self.btn_bw)
        self.disableButton(self.btn_play)
        self.disableButton(self.btn_final)
        self.disableButton(self.btn_clr)
        self.label_msg['text']='arrange, set number , then push [Solve]'
        self.tsumeshg.answer=[]     #Answerをクリア
        self.tsumeshg.answer.append(self.shogi.copyto(Shogi))
        return

    def initbtn_pushed(self):
        self.i_step=0
        self.showSteps()
        self.dispStepNum()
    
    def bwbtn_pushed(self):
        self.i_step -= 1
        self.showSteps()
        self.dispStepNum()
    
    def playbtn_pushed(self):
        self.i_step += 1
        self.showSteps()
        self.dispStepNum()
    
    def finalbtn_pushed(self):
        self.i_step = len(self.tsumeshg.answer)-1
        self.showSteps()
        self.dispStepNum()

    def refreshPlayButtons(self):
        for ibtn in [self.btn_init,self.btn_play,self.btn_bw,self.btn_final]:
            self.enableButton(ibtn)
            
        if self.i_step==0:
            self.disableButton(self.btn_init)
            self.disableButton(self.btn_bw)
        
        if self.i_step==len(self.tsumeshg.answer)-1:
            self.disableButton(self.btn_play)
            self.disableButton(self.btn_final)

    def dispStepNum(self):
        self.label_msg['text']= str(self.i_step)+"手目"

    def showSteps(self):
        self.shogi=Shogi()
        self.tsumeshg.answer[self.i_step].copyto(self.shogi)
        self.refreshDispBan()
        self.refreshDispDai()
        
        self.refreshPlayButtons()
        
        if self.GameMode.get():
            self.curState=self.sts_waiting
            self.deleteAllMarkers()
            self.searchDispCand()
        
        return

    def enableButton(self,button):
        button['state']=tkinter.NORMAL
        button['bg']='pink'
        
    def disableButton(self,button):
        button['state']=tkinter.DISABLED
        button['bg']='gray'  

    def onClikcBan(self,event):
        self.gameState.onClickBan(self,event)

    def onClickBan_arr(self,event):
        #print('on left click: x,y=',event.x,event.y)
        ix,iy = self.__Coordinates2Index(event.x,event.y)
        
        if ix<9 and iy<9:
            if self.curState==self.sts_waiting:
                koma= self.shogi.ban[ix][iy].get_koma()
                if koma:
                    self.selection.koma=koma
                    self.selection.place=koma_select.pban
                    self.selection.ix,self.selection.iy = ix,iy
                    self.selection.owner=koma.owner
                    self.selection.canvas=self.canvas_ban
                    
                    self.dispSelMarkBan(ix,iy,self.imgMarker)

                    self.curState=self.sts_selected
            elif self.curState==self.sts_selected:
                if not self.shogi.ban[ix][iy].get_koma():
                    if self.selection.place==koma_select.pban:
                        self.shogi.warp_koma(self.selection.koma,ix,iy)
                    elif self.selection.place==koma_select.pdaifst:
                        self.shogi.put_koma(fst,self.selection.char,ix,iy)
                        #print('from komadai fst')
                        pass
                    elif self.selection.place==koma_select.pdaisnd:
                        self.shogi.put_koma(snd,self.selection.char,ix,iy)
                        #print('from komadai snd')
                        pass
                    self.deleteAllMarkers()
                    self.curState=self.sts_waiting
                    self.selection=koma_select()
                elif self.selection.place==koma_select.pban and ix==self.selection.ix and iy==self.selection.iy:
                    self.deleteAllMarkers()
                    self.curState=self.sts_waiting
                    self.selection=koma_select()

            self.refreshDispBan()
            self.refreshDispDai()

        else:
            self.refreshDispBan()
            self.refreshDispDai()

    def onClickBan_game(self,event):
        ix,iy = self.__Coordinates2Index(event.x,event.y)

        if self.curState == self.sts_waiting:   #候補手の駒（盤上）を選択されたとき
            newlst = []
            for icand in self.cand[False]:      #クリックされた座標と候補手駒のいずれかが一致するかを調べる
                if [ix,iy] == icand.fromPos:
                    newlst.append(icand)

            if newlst == []:        #候補手の駒が選択されたときのみ処理する。
                return
            
            self.deleteAllMarkers()
            
            self.cand[True]=[]      #打つ候補手は消す
            for i in newlst:
                jx,jy = i.toPos
                self.dispSelMarkBan(jx,jy,self.imgToMarker)
            
            self.cand[False] = newlst
            self.curState=self.sts_selected
            self.dispSelMarkBan(ix,iy,self.imgFromMarker)
        else:
            newlst = []
            for icand in self.cand[True]+self.cand[False]:
                if [ix,iy]== icand.toPos:
                    newlst.append(icand)
            
            if newlst==[]:
                return  #クリックした場所がマーカーのないところのとき：とりあえず何もしない
            
            if len(newlst)==2:  #成と不成があるとき
                answer=messagebox.askquestion("Question","成りますか？")
                for icand in newlst:
                    if icand.isNari == (answer == 'yes'):
                        ope = icand
                        break
            elif len(newlst)==1:
                ope = newlst[0]
                
            else:
                print("Error in onClikcBan_game: newlst items are more than 2")
            self.shogi.DoOperation(ope)
            #手順に追加してPlayボタンの有効無効をリフレッシュする
            self.tsumeshg.answer=self.tsumeshg.answer[0:self.i_step+1]
            cpyshg = Shogi()
            self.shogi.copyto(cpyshg)
            self.tsumeshg.answer.append(cpyshg)
            self.i_step+=1
            self.refreshPlayButtons()
            self.dispStepNum()
            self.enableButton(self.btn_clr)

            self.refreshDispBan()
            self.refreshDispDai()
            
            self.curState=self.sts_waiting
            self.chbx_gameModeCallBack()

    def searchDispCand(self):
        if not self.shogi.isChecked():
            owner=fst
            cands = self.solver2.searchOute(self.shogi)
        else:
            owner=snd
            cands,mudacands = self.solver2.searchUke(self.shogi)
            for cell,mcands in mudacands:
                cands += mcands

        if cands==[]:
            if owner==snd:
                messagebox.showinfo("Message","詰みました。")
            else:
                messagebox.showinfo("Message","王手ができません。")
            #self.GameMode.set(False)
            #self.gameState=StateArrange()
            return

        for i in [True,False]:
            self.cand[i] = []   #candディクショナリをクリアする
        for icand in cands:
            self.cand[icand.isUchi].append(icand)
        
        print("候補手：", self.cand)
        ulst = []
        for icand in self.cand[True]:
            if icand.char not in ulst:
                ulst.append(icand.char)
        lst_char = list(self.shogi.kdai[owner].keys())
        for char in ulst:
            iy = lst_char.index(char)
            self.dispSelMarkDai(self.dicCanv[owner],iy,self.imgToMarker)
                
        mlst = []
        for icand in self.cand[False]:
            if icand.fromPos not in mlst:
                mlst.append(icand.fromPos)
        for ix,iy in mlst:
            self.dispSelMarkBan(ix,iy,self.imgFromMarker)

    def dispSelMarkBan(self,ix,iy,marker):
        x,y=self.__Index2Coordinates(ix,iy)
        self.dicIdMarker[self.canvas_ban].append(self.canvas_ban.create_image(x,y,image=marker))

    def dispSelMarkDai(self,canvas,iy,marker):
        self.dicIdMarker[canvas].append(canvas.create_image(60,60+self.wm*iy,image=marker))

if __name__ == "__main__": 
    gapp=GonkichiApp()
    gapp.setup()

