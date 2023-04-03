import pygame,socket,threading
from pygame.locals import *
from time import sleep
from random import randint

class Piece :
    def __init__(self,j) :
        if j == 2 : self.x,self.y,self.grid = 3,-1,["0000","0000","0000","0000"]
        else : self.x,self.y,self.grid = 3,-1,figures[int(l_pieces[j][0])-1]
    def get_grid(self) : return self.grid
    def left(self) : self.x -= 1
    def right(self) : self.x += 1
    def up(self) : self.y -= 1
    def down(self) : self.y += 1
    def flip_left(self) :
        l = ["","","",""]
        for i in range (4) :
            for j in range (4) :
                l[i] += self.grid[j][-(i+1)]
        self.grid = list(l)
    def flip_right(self) :
        l = ["","","",""]
        for i in range (4) :
            for j in range (3,-1,-1) :
                l[i] += self.grid[j][i]
        self.grid = list(l)

def crea_serveur() :
    global serveur
    global statut
    statut = "serveur"
    serveur = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    serveur.bind((ip,5566))
    thread_connexion = threading.Thread(target=connexion)
    thread_connexion.start()

def crea_client() :
    global client
    global statut
    statut = "client"
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try :
        client.connect((ip,5566))
        data = client.recv(1024)
        data = data.decode("utf8")
        if data == "accept" : return "connection"
        else :
            client.close()
            return "refuse"
    except :
        client.close()
        return "erreur"

def connexion() :
    global ecran
    global serveur
    global client
    while True :
        try :
            serveur.listen()
            nj = serveur.accept()
            sleep(1)
            if ecran == "attente_joueur" :
                client = nj[0]
                thread_mess_client = threading.Thread(target=mess_client)
                thread_mess_client.start()
                client.sendall("accept".encode("utf8"))
                ecran = "chargement"
                affich()
            else : nj.sendall("refuse".encode("utf8"))
        except : break

def mess_serveur() :
    global ecran
    global client
    global l_grilles_aff
    global l_pieces
    global l_en_attente
    global b_act
    global decompte
    while True :
        try :
            data = client.recv(1024)
            data = data.decode("utf8")
            if data.split("/")[0] == "keyrepeat" :
                pygame.key.set_repeat(int(float(data.split("/")[1])*1000),int(float(data.split("/")[1])*1000))
                if ecran == "chargement" : client.sendall("getparam2".encode("utf8"))
            elif data.split("/")[0] == "grille" :
                l_grilles_aff = [data.split("/")[2].split(","),data.split("/")[1].split(",")]
                if ecran == "chargement" : client.sendall("getparam3".encode("utf8"))
                else : affich()
            elif data.split("/")[0] == "pieces" :
                l_pieces = [[data.split("/")[2]],[data.split("/")[1]]]
                if ecran == "chargement" : client.sendall("getparam4".encode("utf8"))
                else : affich()
            elif data.split("/")[0] == "lenattente" :
                l_en_attente = [float(data.split("/")[2]),float(data.split("/")[1])]
                if ecran == "chargement" :
                    client.sendall("ok".encode("utf8"))
                    ecran,decompte = "decompte",""
                affich()
            elif data in ["3","2","1","C'est parti !"] :
                decompte = data
                affich()
            elif data == "go" :
                ecran = "jeu"
                affich()
            elif data in ["victoire","defaite"] :
                ecran,b_act = data,0
                affich()
        except : break

def mess_client() :
    global ecran
    global client
    global l_grilles
    global l_pieces
    global l_en_attente
    global piece_j
    global decompte
    while True :
        try :
            data = client.recv(1024)
            data = data.decode("utf8")
            if data == "getparam1" :
                sleep(0.1)
                client.sendall(("keyrepeat/"+param["delai_key"]).encode("utf8"))
            elif data == "getparam2" :
                sleep(0.1)
                piece_j = [Piece(2),Piece(2)]
                l_grilles = [["0000000000" for j in range (20)] for i in range (2)]
                send_grilles()
            elif data == "getparam3" :
                sleep(0.1)
                l = [str(randint(1,7)) for j in range (2)]
                l_pieces = [list(l),list(l)]
                send_pieces()
            elif data == "getparam4" :
                sleep(0.1)
                l_en_attente = [0,0]
                send_l_en_attente()
            elif data == "ok" :
                ecran,decompte = "decompte",""
                affich()
                for i in range (4) :
                    sleep(1)
                    decompte = ["3","2","1","C'est parti !"][i]
                    client.sendall(decompte.encode("utf8"))
                    affich()
                sleep(1)
                nouvelle_piece(0)
                nouvelle_piece(1)
                send_pieces()
                send_grilles()
                client.sendall("go".encode("utf8"))
                ecran = "jeu"
                affich()
                pygame.key.set_repeat(int(float(param["delai_key"])*1000),int(float(param["delai_key"])*1000))
                thread_move_pieces_j1 = threading.Thread(target=lambda x=0:move_pieces(x))
                thread_move_pieces_j1.start()
                thread_move_pieces_j2 = threading.Thread(target=lambda x=1:move_pieces(x))
                thread_move_pieces_j2.start()
            else : move(1,data)
        except : break

def move_pieces(j) :
    global piece_j
    while ecran == "jeu" :
        sleep(float(param["delai_chute"]))
        piece_j[j].down()
        if test_obstacle(j) == 1 :
            piece_j[j].up()
            impression_piece(j)
            suppr_lignes(j)
            nouvelle_piece(j)
        send_grilles()
        send_pieces()
        send_l_en_attente()

def suppr_lignes(j) :
    global l_grilles
    global l_en_attente
    global piece_j
    l_suppr = []
    for i in range (20) :
        if not "0" in l_grilles[j][i] : l_grilles[j][i],l_suppr = "0000000000",l_suppr+[i]
    piece_j[j] = Piece(2)
    send_grilles()
    send_pieces()
    sleep(float(param["delai_destruction"]))
    for i in range (len(l_suppr)-1,-1,-1) :
        del l_grilles[j][l_suppr[i]]
    for i in range (len(l_suppr)) :
        l_grilles[j] = ["0000000000"]+l_grilles[j]
    if len(l_suppr) > 0 :
        n = float(param["valeur_l"+str(len(l_suppr))])
        if l_en_attente[j] > 0 :
            if n >= l_en_attente[j] : l_en_attente[j],n = 0,n-l_en_attente[j]
            else : l_en_attente[j],n = l_en_attente[j]-n,0
        if n > 0 : l_en_attente[1-j] += n
        if l_en_attente[1-j] > 20 : l_en_attente[1-j] = 20
        send_l_en_attente()
    send_grilles()

def nouvelle_piece(j) :
    global ecran
    global l_pieces
    global piece_j
    global b_act
    piece_j[j] = Piece(j)
    del l_pieces[j][0]
    if len(l_pieces[0]) <= 1 or len(l_pieces[1]) <= 1 :
        p = str(randint(1,7))
        l_pieces[0],l_pieces[1] = l_pieces[0]+[p],l_pieces[1]+[p]
    if test_obstacle(j) == 1 :
        ecran,b_act = ["defaite","victoire"][j],0
        sleep(0.1)
        client.sendall(["victoire","defaite"][j].encode("utf8"))

def send_pieces() :
    client.sendall(("pieces/"+l_pieces[0][0]+"/"+l_pieces[1][0]+"/").encode("utf8"))
    affich()

def send_grilles() :
    global l_grilles_aff
    l_grilles_aff = [list(i) for i in l_grilles]
    for i in range (2) :
        for j in range (4) :
            for k in range (4) :
                if 0 <= piece_j[i].x+k < 10 and 0 <= piece_j[i].y+j < 20 and piece_j[i].get_grid()[j][k] != "0" : l_grilles_aff[i][piece_j[i].y+j] = l_grilles_aff[i][piece_j[i].y+j][:piece_j[i].x+k]+piece_j[i].get_grid()[j][k]+l_grilles_aff[i][piece_j[i].y+j][piece_j[i].x+k+1:]
    client.sendall(("grille/"+"/".join([",".join(i) for i in l_grilles_aff])+"/").encode("utf8"))
    affich()

def send_l_en_attente() :
    client.sendall(("lenattente/"+str(l_en_attente[0])+"/"+str(l_en_attente[1])+"/").encode("utf8"))
    affich()

def move(j,m) :
    global piece_j
    if m == "up" :
        piece_j[j].down()
        while test_obstacle(j) == 0 : piece_j[j].down()
        piece_j[j].up()
        impression_piece(j)
        suppr_lignes(j)
        nouvelle_piece(j)
    elif m == "down" :
        piece_j[j].down()
        if test_obstacle(j) == 1 :
            piece_j[j].up()
            impression_piece(j)
            suppr_lignes(j)
            nouvelle_piece(j)
    elif m == "left" :
        piece_j[j].left()
        non = test_obstacle(j)
        if non == 1 : piece_j[j].right()
    elif m == "right" :
        piece_j[j].right()
        non = test_obstacle(j)
        if non == 1 : piece_j[j].left()
    elif m == "flip_left" :
        piece_j[j].flip_left()
        non = test_obstacle(j)
        if non == 1 : piece_j[j].flip_right()
    elif m == "flip_right" :
        piece_j[j].flip_right()
        non = test_obstacle(j)
        if non == 1 : piece_j[j].flip_left()
    send_grilles()
    if m in ["up","down"] : send_pieces()
    affich()

def test_obstacle(j) :
    non = 0
    for i in range (4) :
        for k in range (4) :
            if (not 0 <= piece_j[j].x+k < 10 or not 0 <= piece_j[j].y+i < 20) and piece_j[j].get_grid()[i][k] != "0" or 0 <= piece_j[j].x+k < 10 and 0 <= piece_j[j].y+i < 20 and l_grilles[j][piece_j[j].y+i][piece_j[j].x+k] != "0" and piece_j[j].get_grid()[i][k] != "0" :
                non = 1
                break
    return non

def impression_piece(j) :
    global l_grilles
    global l_en_attente
    for i in range (4) :
        for k in range (4) :
            if 0 <= piece_j[j].x+k < 10 and 0 <= piece_j[j].y+i < 20 and piece_j[j].get_grid()[i][k] != "0" : l_grilles[j][piece_j[j].y+i] = l_grilles[j][piece_j[j].y+i][:piece_j[j].x+k]+piece_j[j].get_grid()[i][k]+l_grilles[j][piece_j[j].y+i][piece_j[j].x+k+1:]
    if l_en_attente[j] > 0 :
        c = randint(0,9)
        l_grilles[j] += ["8"*c+"0"+"8"*(9-c)]*int(l_en_attente[j])
        del l_grilles[j][:int(l_en_attente[j])]
        l_en_attente[j] = 0
        send_l_en_attente()

def affich() :
    if ecran == "titre" :
        pygame.draw.rect(fenetre,(127,127,127),(0,0,largeur,hauteur))
        myfont = pygame.font.SysFont("Courier",96)
        texte = myfont.render("TETRIS VERSUS",False,(170,20,170))
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur/2-texte.get_height()-10))
        myfont = pygame.font.SysFont("Courier",12)
        texte = myfont.render("Aide (a)",False,(0,0,0))
        fenetre.blit(texte,(10,hauteur-texte.get_height()-10))
        myfont = pygame.font.SysFont("Courier",24)
        texte = myfont.render("Créer une partie",False,[(0,0,0),(255,255,255),(0,0,0)][b_act])
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur/2+10))
        myfont = pygame.font.SysFont("Courier",24)
        texte = myfont.render("Rejoindre une partie",False,[(0,0,0),(0,0,0),(255,255,255)][b_act])
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur/2+texte.get_height()+20))

    elif ecran == "param_partie" :
        pygame.draw.rect(fenetre,(127,127,127),(0,0,largeur,hauteur))
        myfont = pygame.font.SysFont("Courier",24)
        j = 0
        for i in param :
            texte = myfont.render({"delai_chute" : "Délai de la chute des pieces","delai_key" : "Délai des actions","delai_destruction" : "Délai de la disparition des lignes","valeur_l1" : "Valeur de la destruction de 1 lignes","valeur_l2" : "Valeur de la destruction de 2 lignes","valeur_l3" : "Valeur de la destruction de 3 lignes","valeur_l4" : "Valeur de la destruction de 4 lignes"}[i]+" : "+str(param[i])+" "+{"delai_chute" : "s","delai_key" : "s","delai_destruction" : "s","valeur_l1" : "lignes","valeur_l2" : "lignes","valeur_l3" : "lignes","valeur_l4" : "lignes"}[i],False,(0,0,0))
            c = (255,255,255) if b_act == i+"-" else (0,0,0)
            pygame.draw.rect(fenetre,c,(largeur/2-texte.get_width()/2-20,hauteur/2-texte.get_height()*3.5+texte.get_height()*j+12,10,2))
            c = (255,255,255) if b_act == i+"+" else (0,0,0)
            pygame.draw.rect(fenetre,c,(largeur/2+texte.get_width()/2+10,hauteur/2-texte.get_height()*3.5+texte.get_height()*j+12,10,2))
            pygame.draw.rect(fenetre,c,(largeur/2+texte.get_width()/2+14,hauteur/2-texte.get_height()*3.5+texte.get_height()*j+8,2,10))
            fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur/2-texte.get_height()*3.5+texte.get_height()*j))
            j += 1
        if b_act == 1 : texte = myfont.render("Ok",False,(255,255,255))
        else : texte = myfont.render("Ok",False,(0,0,0))
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur-texte.get_height()*2-20))
        if b_act == 2 : texte = myfont.render("Annuler",False,(255,255,255))
        else : texte = myfont.render("Annuler",False,(0,0,0))
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur-texte.get_height()-10))

    elif ecran == "attente_joueur" :
        pygame.draw.rect(fenetre,(127,127,127),(0,0,largeur,hauteur))
        myfont = pygame.font.SysFont("Courier",36)
        texte = myfont.render("Nom de la partie : "+ip,False,(0,0,0))
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur/2-texte.get_height()-10))
        texte = myfont.render("En attente d'un joueur...",False,(0,0,0))
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur/2+10))
        myfont = pygame.font.SysFont("Courier",24)
        texte = myfont.render("Annuler",False,[(0,0,0),(255,255,255)][b_act])
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur-texte.get_height()-10))

    elif ecran == "rejoindre_partie" :
        pygame.draw.rect(fenetre,(127,127,127),(0,0,largeur,hauteur))
        myfont = pygame.font.SysFont("Courier",36)
        texte = myfont.render("Nom de la partie :",False,(0,0,0))
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur/2-texte.get_height()-10))
        texte = myfont.render("W",False,(0,0,0))
        pygame.draw.rect(fenetre,(0,0,0),(largeur/2-texte.get_width()*7.5-2,hauteur/2+8,texte.get_width()*15+4,texte.get_height()+4))
        pygame.draw.rect(fenetre,(255,255,255),(largeur/2-texte.get_width()*7.5,hauteur/2+10,texte.get_width()*15,texte.get_height()))
        texte2 = myfont.render(ip,False,(0,0,0))
        fenetre.blit(texte2,(largeur/2-texte.get_width()*7.5,hauteur/2+10))
        myfont = pygame.font.SysFont("Courier",24)
        texte = myfont.render("Rejoindre",False,[(0,0,0),(255,255,255),(0,0,0)][b_act])
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur-texte.get_height()*2-20))
        texte = myfont.render("Annuler",False,[(0,0,0),(0,0,0),(255,255,255)][b_act])
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur-texte.get_height()-10))

    elif ecran == "erreur_connexion" :
        pygame.draw.rect(fenetre,(0,0,0),(0,0,largeur,hauteur))
        myfont = pygame.font.SysFont("Courier",24)
        texte = myfont.render("Cette partie n'existe pas",False,(255,0,0))
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur/2-texte.get_height()/2))

    elif ecran == "erreur_refuse" :
        pygame.draw.rect(fenetre,(0,0,0),(0,0,largeur,hauteur))
        myfont = pygame.font.SysFont("Courier",24)
        texte = myfont.render("Vous ne pouvez pas rejoindre cette partie",False,(255,0,0))
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur/2-texte.get_height()/2))

    elif ecran == "chargement" :
        pygame.draw.rect(fenetre,(0,0,0),(0,0,largeur,hauteur))
        myfont = pygame.font.SysFont("Courier",24)
        texte = myfont.render("Chargement...",False,(255,255,255))
        fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur/2-texte.get_height()/2))

    elif ecran in ["decompte","jeu","victoire","defaite"] :
        pygame.draw.rect(fenetre,(127,127,127),(0,0,largeur,hauteur))
        if largeur/2 <= hauteur-100 : taille = largeur/4
        else : taille = (hauteur-100)/2
        pygame.draw.rect(fenetre,(255,255,255),(largeur/4-taille/2-5,hauteur/2-taille-5,taille+10,taille*2+10))
        pygame.draw.rect(fenetre,(255,255,255),(largeur/4*3-taille/2-5,hauteur/2-taille-5,taille+10,taille*2+10))
        pygame.draw.rect(fenetre,(255,255,255),(largeur/4+taille/2,hauteur/2-taille-5,taille/10*4+20,taille/10*4+20))
        pygame.draw.rect(fenetre,(0,0,0),(largeur/4+taille/2+5,hauteur/2-taille,taille/10*4+10,taille/10*4+10))
        pygame.draw.rect(fenetre,(255,255,255),(largeur/4*3-taille/2-(taille/10*4+20),hauteur/2-taille-5,taille/10*4+20,taille/10*4+20))
        pygame.draw.rect(fenetre,(0,0,0),(largeur/4*3-taille/2-(taille/10*4+15),hauteur/2-taille,taille/10*4+10,taille/10*4+10))
        for i in range (10) :
            pygame.draw.rect(fenetre,[(0,0,128),(0,0,255)][i%2],(largeur/4-taille/2+i*(taille/10),hauteur/2-taille,taille/10+1,taille*2))
            pygame.draw.rect(fenetre,[(0,0,128),(0,0,255)][i%2],(largeur/4*3-taille/2+i*(taille/10),hauteur/2-taille,taille/10+1,taille*2))
        for i in range (4) :
            for j in range (4) :
                if figures[int(l_pieces[0][0])-1][i][j] != "0" : pygame.draw.rect(fenetre,[(190,30,30),(240,210,30),(255,130,15),(50,190,220),(40,50,190),(140,50,140),(40,140,30),(200,200,200)][int(figures[int(l_pieces[0][0])-1][i][j])-1],(largeur/4+taille/2+12+taille/10*j,hauteur/2-taille+12+taille/10*i,taille/10-4,taille/10-4))
                if figures[int(l_pieces[1][0])-1][i][j] != "0" : pygame.draw.rect(fenetre,[(190,30,30),(240,210,30),(255,130,15),(50,190,220),(40,50,190),(140,50,140),(40,140,30),(200,200,200)][int(figures[int(l_pieces[1][0])-1][i][j])-1],(largeur/4*3-taille/2-(taille/10*4+10)+taille/10*j,hauteur/2-taille+12+taille/10*i,taille/10-4,taille/10-4))
        if ecran == "decompte" :
            myfont = pygame.font.SysFont("Courier",72)
            texte = myfont.render(decompte,False,(255,255,255))
            fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur/2-texte.get_height()/2))
        elif ecran in ["jeu","victoire","defaite"] :
            for i in range (20) :
                for j in range (10) :
                    if l_grilles_aff[0][i][j] != "0" :
                        pygame.draw.rect(fenetre,(0,0,0),(largeur/4-taille/2+j*taille/10,hauteur/2-taille+i*taille/10,taille/10+1,taille/10+1))
                        pygame.draw.rect(fenetre,[(190,30,30),(240,210,30),(255,130,15),(50,190,220),(40,50,190),(140,50,140),(40,140,30),(200,200,200)][int(l_grilles_aff[0][i][j])-1],(largeur/4-taille/2+j*taille/10+2,hauteur/2-taille+i*taille/10+2,taille/10-3,taille/10-3))
                    if l_grilles_aff[1][i][j] != "0" :
                        pygame.draw.rect(fenetre,(0,0,0),(largeur/4*3-taille/2+j*taille/10,hauteur/2-taille+i*taille/10,taille/10+1,taille/10+1))
                        pygame.draw.rect(fenetre,[(190,30,30),(240,210,30),(255,130,15),(50,190,220),(40,50,190),(140,50,140),(40,140,30),(200,200,200)][int(l_grilles_aff[1][i][j])-1],(largeur/4*3-taille/2+j*taille/10+2,hauteur/2-taille+i*taille/10+2,taille/10-3,taille/10-3))
            for i in range (int(l_en_attente[0])) :
                pygame.draw.rect(fenetre,(40,180,80),(largeur/4+taille/2+10,hauteur/2+taille+1-(i+1)*taille/20,taille/20-1,taille/20-1))
            for i in range (int(l_en_attente[1])) :
                pygame.draw.rect(fenetre,(40,180,80),(largeur/4*3-taille/2-9-taille/20,hauteur/2+taille+1-(i+1)*taille/20,taille/20-1,taille/20-1))
            if ecran == "victoire" :
                cache = pygame.Surface((taille,taille*2))
                cache.set_alpha(150)
                cache.fill((0,0,0))
                fenetre.blit(cache,(largeur/4*3-taille/2,hauteur/2-taille))
            elif ecran == "defaite" :
                cache = pygame.Surface((taille,taille*2))
                cache.set_alpha(150)
                cache.fill((0,0,0))
                fenetre.blit(cache,(largeur/4-taille/2,hauteur/2-taille))
            if ecran in ["victoire","defaite"] :
                myfont = pygame.font.SysFont("Courier",36)
                texte = myfont.render({"victoire" : "Vous avez gagné !","defaite" : "Vous avez perdu..."}[ecran],False,(0,0,0))
                myfont = pygame.font.SysFont("Courier",24)
                texte2 = myfont.render("Quitter",False,[(0,0,0),(255,255,255)][b_act])
                pygame.draw.rect(fenetre,(255,255,255),(largeur/2-texte.get_width()/2-5,hauteur/2-texte.get_height()-5,texte.get_width()+10,texte.get_height()+texte2.get_height()+10))
                pygame.draw.rect(fenetre,(127,127,127),(largeur/2-texte.get_width()/2,hauteur/2-texte.get_height(),texte.get_width(),texte.get_height()+texte2.get_height()))
                fenetre.blit(texte,(largeur/2-texte.get_width()/2,hauteur/2-texte.get_height()))
                fenetre.blit(texte2,(largeur/2-texte2.get_width()/2,hauteur/2))

    pygame.display.flip()

pygame.init()

largeur,hauteur = pygame.display.Info().current_w,pygame.display.Info().current_h
fenetre = pygame.display.set_mode((largeur,hauteur),RESIZABLE)
pygame.display.set_caption("Tetris Versus")

ecran,statut,b_act,figures,param = "titre","",0,[["0000","1111","0000","0000"],["0000","0222","0200","0000"],["0000","3330","0030","0000"],["0000","0440","0440","0000"],["0000","5550","0500","0000"],["0000","0660","6600","0000"],["0000","7700","0770","0000"]],{"delai_chute" : "1.0","delai_key" : "0.1","delai_destruction" : "1.0","valeur_l1" : "0.50","valeur_l2" : "1.00","valeur_l3" : "1.50","valeur_l4" : "2.00"}
affich()

pygame.key.set_repeat(100,100)

b = 1
while b == 1 :
    for event in pygame.event.get() :
        if event.type == QUIT :
            b = 0
            pygame.quit()
            try : serveur.close()
            except : ""
            try : client.close()
            except : ""

        elif event.type == VIDEORESIZE :
            largeur,hauteur = event.w,event.h
            affich()

        elif event.type == MOUSEMOTION :
            myfont = pygame.font.SysFont("Courier New",24)
            texte,texte2 = myfont.render("Créer une partie",False,(255,255,255)),myfont.render("Rejoindre une partie",False,(255,255,255))
            if ecran == "titre" :
                if largeur/2-texte.get_width()/2 < event.pos[0] < largeur/2+texte.get_width()/2 and hauteur/2+10 < event.pos[1] < hauteur/2+texte.get_height()+10 : b_act = 1
                elif largeur/2-texte2.get_width()/2 < event.pos[0] < largeur/2+texte2.get_width()/2 and hauteur/2+texte2.get_height()+20 < event.pos[1] < hauteur/2+texte2.get_height()*2+20 : b_act = 2
                else : b_act = 0
            elif ecran == "param_partie" :
                myfont = pygame.font.SysFont("Courier",24)
                j,non = 0,0
                for i in param :
                    texte = myfont.render({"delai_chute" : "Délai de la chute des pieces","delai_key" : "Délai des actions","delai_destruction" : "Délai de la disparition des lignes","valeur_l1" : "Valeur de la destruction de 1 lignes","valeur_l2" : "Valeur de la destruction de 2 lignes","valeur_l3" : "Valeur de la destruction de 3 lignes","valeur_l4" : "Valeur de la destruction de 4 lignes"}[i]+" : "+str(param[i])+" "+{"delai_chute" : "s","delai_key" : "s","delai_destruction" : "s","valeur_l1" : "lignes","valeur_l2" : "lignes","valeur_l3" : "lignes","valeur_l4" : "lignes"}[i],False,(0,0,0))
                    if largeur/2-texte.get_width()/2-20 < event.pos[0] < largeur/2-texte.get_width()/2-10 and hauteur/2-texte.get_height()*3.5+texte.get_height()*j+8 < event.pos[1] < hauteur/2-texte.get_height()*3.5+texte.get_height()*j+18 :
                        b_act,non = i+"-",1
                        break
                    if largeur/2+texte.get_width()/2+10 < event.pos[0] < largeur/2+texte.get_width()/2+20 and hauteur/2-texte.get_height()*3.5+texte.get_height()*j+8 < event.pos[1] < hauteur/2-texte.get_height()*3.5+texte.get_height()*j+18 :
                        b_act,non = i+"+",1
                        break
                    j += 1
                if non == 0 :
                    texte,texte2 = myfont.render("Ok",False,(0,0,0)),myfont.render("Annuler",False,(0,0,0))
                    if largeur/2-texte.get_width()/2 < event.pos[0] < largeur/2+texte.get_width()/2 and hauteur-texte.get_height()*2-20 < event.pos[1] < hauteur-texte.get_height()-20 : b_act = 1
                    elif largeur/2-texte2.get_width()/2 < event.pos[0] < largeur/2+texte2.get_width()/2 and hauteur-texte.get_height()-10 < event.pos[1] < hauteur-10 : b_act = 2
                    else : b_act = 0
            elif ecran == "attente_joueur" :
                myfont = pygame.font.SysFont("Courier New",24)
                texte = myfont.render("Annuler",False,[(255,255,255),(255,0,0)][b_act])
                if largeur/2-texte.get_width()/2 < event.pos[0] < largeur/2+texte.get_width()/2 and hauteur-texte.get_height()-10 < event.pos[1] < hauteur-10 : b_act = 1
                else : b_act = 0
            elif ecran == "rejoindre_partie" :
                myfont = pygame.font.SysFont("Courier New",24)
                texte,texte2 = myfont.render("Rejoindre",False,[(0,0,0),(255,255,255),(0,0,0)][b_act]),myfont.render("Annuler",False,[(0,0,0),(0,0,0),(255,255,255)][b_act])
                if largeur/2-texte.get_width()/2 < event.pos[0] < largeur/2+texte.get_width()/2 and hauteur-texte.get_height()*2-20 < event.pos[1] < hauteur-texte.get_height()-20 : b_act = 1
                elif largeur/2-texte2.get_width()/2 < event.pos[0] < largeur/2+texte2.get_width()/2 and hauteur-texte.get_height()-10 < event.pos[1] < hauteur-10 : b_act = 2
                else : b_act = 0
            elif ecran in ["victoire","defaite"] :
                myfont = pygame.font.SysFont("Courier",24)
                texte = myfont.render("Quitter",False,(0,0,0))
                if largeur/2-texte.get_width()/2 < event.pos[0] < largeur/2+texte.get_width()/2 and hauteur/2 < event.pos[1] < hauteur/2+texte.get_height() : b_act = 1
                else : b_act = 0
            if ecran in ["titre","param_partie","attente_joueur","rejoindre_partie","victoire","defaite"] : affich()

        elif event.type == MOUSEBUTTONDOWN and event.button == 1 :
            if ecran == "titre" :
                if b_act == 1 : ecran,b_act = "param_partie",0
                elif b_act == 2 : ecran,ip,b_act = "rejoindre_partie","",0
                if ecran != "titre" : affich()
            elif ecran == "param_partie" :
                if b_act == 1 :
                    ecran,ip,b_act = "attente_joueur",socket.gethostbyname(socket.gethostname()),0
                    crea_serveur()
                elif b_act == 2 : ecran,b_act = "titre",0
                elif b_act != 0 and not (float(param[b_act[:-1]]) <= 0 and b_act[-1] == "-") :
                    param[b_act[:-1]] = str(float(param[b_act[:-1]])+float(b_act[-1]+{"delai_chute" : "0.1","delai_key" : "0.1","delai_destruction" : "0.1","valeur_l1" : "0.25","valeur_l2" : "0.25","valeur_l3" : "0.25","valeur_l4" : "0.25"}[b_act[:-1]]))
                    if b_act[:-1] in ["delai_chute","delai_key","delai_destruction"] : param[b_act[:-1]] = str(int(float(param[b_act[:-1]])*10+0.05)/10)
                affich()
            elif ecran == "attente_joueur" and b_act == 1 :
                serveur.close()
                ecran,b_act = "titre",0
                affich()
            elif ecran == "rejoindre_partie" :
                if b_act == 1 :
                    rep = crea_client()
                    if rep == "erreur" : ecran,b_act = "erreur_connexion",0
                    elif rep == "refuse" : ecran,b_act = "erreur_refuse",0
                    elif rep == "connection" :
                        ecran,b_act = "chargement",0
                        thread_mess_serveur = threading.Thread(target=mess_serveur)
                        thread_mess_serveur.start()
                        client.sendall("getparam1".encode("utf8"))
                elif b_act == 2 : ecran,b_act = "titre",0
                if ecran != "rejoindre_partie" : affich()
            elif ecran in ["erreur_connexion","erreur_refuse"] :
                ecran = "rejoindre_partie"
                affich()
            elif ecran in ["victoire","defaite"] and b_act == 1 :
                ecran,b_act = "titre",0
                client.close()
                if statut == "serveur" : serveur.close()

        elif event.type == KEYDOWN :
            if ecran == "titre" and event.key == K_q :
                myfont = pygame.font.SysFont("Courier New",12)
                for i in range (6) :
                    texte = myfont.render(["Bouger à gauche -> flèche de gauche","Bouger à droite -> flèche de droite","Bouger vers le bas -> flèche du bas","Poser la pièce immédiatement -> flèche du haut","Tourner vers la gauche -> a","Tourner vers la droite -> z"][i],False,(0,0,0))
                    fenetre.blit(texte,(10,10+texte.get_height()*i))
                pygame.display.flip()
            elif ecran == "rejoindre_partie" :
                if len(ip) < 15 and event.unicode != "" and event.unicode in "0123456789." : ip += event.unicode
                elif event.key == 8 and len(ip) > 0 : ip = ip[:-1]
                affich()
            elif ecran == "jeu" and event.key in [K_UP,K_DOWN,K_LEFT,K_RIGHT,K_q,K_w] :
                if statut == "client" : client.sendall({K_UP : "up",K_DOWN : "down",K_LEFT : "left",K_RIGHT : "right",K_q : "flip_left",K_w : "flip_right"}[event.key].encode("utf8"))
                else : move(0,{K_UP : "up",K_DOWN : "down",K_LEFT : "left",K_RIGHT : "right",K_q : "flip_left",K_w : "flip_right"}[event.key])