# -*- coding: UTF-8 -*-
# Copyright (C) 2012  Governo do Estado do Rio Grande do Sul
#
#   Author: Sergio Berlotto <sergio.berlotto@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, flash, jsonify, send_from_directory, \
     make_response
from flaskext.uploads import UploadSet
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)
import sys
import os
import time
import re
from shutil import copyfile
from stat import *
from werkzeug import secure_filename

#Actual directory
PWD = os.path.dirname(os.path.realpath(__file__))

#---------------------------------------------------------------------
UPLOADED_FILES_DEST = os.path.join(PWD, 'uploads')
UPLOADED_FILES_ALLOW = set(['ogg', 'ogv', 'webm', 'mp4'])
UPLOADED_FILES_DENY = ''
APP_PORT = 8000
APP_HOST = "0.0.0.0"
APP_URL = 'localhost:8000'
SECRET_KEY = "yeah, not actually a secret"
DEFAULT_VIDEO_SIZE = '500x400' #Tamanho default, width:height
DEFAULT_VIDEO_POSTER = 'default_poster.png'
#---------------------------------------------------------------------

try:
    from conf import *
except:
    pass

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOADED_FILES_DEST
app.config['URL'] = APP_URL
app.config['SECRET_KEY'] = SECRET_KEY

UPLOADED_FILES_ALLOW = ('ogg', 'ogv', 'webm', 'mp4')
videos = UploadSet('videos', UPLOADED_FILES_ALLOW)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Necess&aacute;rio efetuar o login.'
login_manager.setup_app(app)

#---------------------------------------------------------------------


@app.route("/secret")
@fresh_login_required
def secret():
    return render_template("secret.html")


class User(UserMixin):

    def __init__(self, id, senha, nome=''):
        self.usuarioid = id
        self.senha = senha
        self.nome = nome

    def senha_valida(self, senha_form):
        return senha_form and senha_form == self.senha

    def is_authenticated(self):
        return True

    def is_active(self):
        for user in USUARIOS:
            if user[0] == self.usuarioid:
                return True
        else:
            return False

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.usuarioid


try:
    from user_list import USUARIOS
    LISTA_USUARIOS = {}
    for x in USUARIOS:
        LISTA_USUARIOS[x[0]] = User(x[0], x[1], x[2])
except:
    print "A lista de usuarios nao esta configurada ou disponivel"
    raise


@login_manager.user_loader
def load_user(userid):
    return LISTA_USUARIOS[userid]


def getUsuariosId():
    return [u[0] for u in USUARIOS]


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        username = request.form["username"]
        senha = request.form["password"]
        if username in getUsuariosId():
            u = LISTA_USUARIOS[username]
            if u.senha_valida(senha):
                remember = request.form.get("remember", "no") == "yes"
                if login_user(u, remember=remember):
                    flash("Logged in!")
                    return redirect(request.args.get("next") or url_for("index"))
                else:
                    flash("Sorry, but you could not log in.")
        else:
            flash(u"Invalid username.")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('login')

#---------------------------------------------------------------------


def allowed_file(filename):
    '''
    Verifica as extensoes permitidas para os videos.
    '''
    return '.' in filename and filename.rsplit('.', 1)[1] in UPLOADED_FILES_ALLOW


def getSize(size):
    '''
    Retorna o tamanho de um arquivo, em formato humano.
    '''
    if (size > 1024 * 1024):
        bytesTransfered = str(round(size * 100 / (1024 * 1024)) / 100) + 'MB'
    elif(size > 1024):
        bytesTransfered = str(round(size * 100 / 1024) / 100) + 'KB'
    else:
        bytesTransfered = str(round(size * 100) / 100) + 'Bytes'
    return bytesTransfered


def has_poster(filename):
    '''
    Verifica se o video tem imagem de poster.
    '''
    f = re.compile('^poster_%s' % filename)
    for dirname, dirnames, filenames in os.walk(UPLOADED_FILES_DEST):
        for filename in filenames:
            if f.match(filename):
                return True
    return False


def getDimension(filename):
    '''
    Le o arquivo de configuracao do video e retorna os valores para WIDTH e HEIGHT
    '''
    f = open(os.path.join(app.config['UPLOAD_FOLDER'], "%s.txt" % filename[:-4]))
    linha = f.readline()
    width, height = [int(x) for x in linha.split('=')[1].split("x")]
    return width, height
#---------------------------------------------------------------------


@app.route('/')
@login_required
def index():
    return render_template('index.html', current_user=current_user)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if len(request.files) <= 0:
            return "Voc&ecirc; n&atilde;o enviou nenhum v&iacute;deo."
        try:
            f = request.files['fileToUpload']
            if allowed_file(f.filename):
                filename = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                #Grava as informacoes adicionais em um arquivo texto
                file_infos = open("%s.txt" % os.path.join(app.config['UPLOAD_FOLDER'], filename)[:-4], 'w')
                if(request.form['size'] and request.form['size'] != 'x'):
                    file_infos.write("SIZE=%s" % request.form['size'])
                else:
                    file_infos.write("SIZE=%s" % DEFAULT_VIDEO_SIZE)
                file_infos.close()
                #Trata o poster
                if len(request.files) > 1:
                    if request.files['poster']:
                        poster_file = request.files['poster']
                        pFileName = "poster_%s_%s" % (secure_filename(filename), secure_filename(poster_file.filename))
                        poster_file.save(os.path.join(app.config['UPLOAD_FOLDER'], pFileName))
                else:
                    pFileName = "poster_%s_%s" % (secure_filename(filename), secure_filename(DEFAULT_VIDEO_POSTER))
                    copyfile(os.path.join(app.config['UPLOAD_FOLDER'], DEFAULT_VIDEO_POSTER),
                             os.path.join(app.config['UPLOAD_FOLDER'], pFileName))
                return "Seu arquivo <i>%s</i> foi recebido com sucesso!" % filename
            else:
                return "Exten&ccedil;&atilde;o de arquivo n&atilde;o permitida!"
            return redirect(url_for('show', name=filename))
        except:
            for arg in sys.argv[1:]:
                try:
                    f = open(arg, 'r')
                except IOError:
                    print 'cannot open', arg
                else:
                    print arg, 'has', len(f.readlines()), 'lines'
                    f.close()
            raise
        return render_template('index.html')


@app.route('/lista-videos')
@login_required
def lista():
    arquivos = []
    for dirname, dirnames, filenames in os.walk(UPLOADED_FILES_DEST):
        for filename in filenames:
            if allowed_file(filename):
                st = os.stat(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                arquivos.append({'filename': filename, 'size': getSize(st[ST_SIZE]),
                                 'date': time.asctime(time.localtime(st[ST_MTIME])),
                                 'poster': has_poster(filename)})
    return render_template('fileitem.html', files=arquivos, url=app.config['URL'])


@app.route('/v/<filename>')
def show(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/poster/<filename>')
def show_p(filename):
    f = re.compile('^poster_%s' % filename)
    for dirname, dirnames, filenames in os.walk(UPLOADED_FILES_DEST):
        for filename in filenames:
            if f.match(filename):
                return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    return None


@app.route('/poster/view/<filename>')
def view_p(filename):
    return render_template('poster.html', filename=filename, url=app.config['URL'])


@app.route('/play/<filename>')
def player(filename):
    w, h = getDimension(filename)
    return render_template('play.html', filename=filename, w=w, h=h, poster=has_poster(filename), url=app.config['URL'])


@app.route('/snippet/<filename>')
def snippet(filename):
    w, h = getDimension(filename)
    response = make_response(render_template('snippet.html', filename=filename, w=w, h=h, url=app.config['URL']))
    response.headers["Content-type"] = "text/plain"
    return response
    #return render_template('snippet.html', filename=filename)


@app.route('/delete/<videoname>')
def delete(videoname):
    #deleta o video
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], videoname))
    #deleta o poster
    f = re.compile('^poster_%s' % videoname)
    for dirname, dirnames, filenames in os.walk(UPLOADED_FILES_DEST):
        for filename in filenames:
            if f.match(filename):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                break
    #deleta o arquivo do tamanho do video
    os.remove("%s.txt" % os.path.join(app.config['UPLOAD_FOLDER'], videoname)[:-4])
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=False, port=APP_PORT, host=APP_HOST)
