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
import sys
import os
import time
import re
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
#---------------------------------------------------------------------

try:
    from conf import *
except:
    pass

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOADED_FILES_DEST
app.config['URL'] = APP_URL

UPLOADED_FILES_ALLOW = ('ogg', 'ogv', 'webm', 'mp4')
videos = UploadSet('videos', UPLOADED_FILES_ALLOW)

#---------------------------------------------------------------------


def allowed_file(filename):
    '''
    Verifica as extensoes permitidas para os videos.
    '''
    print "Verifiing %s " % filename
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
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    #print "Uploading..."
    if request.method == 'POST':
        print "Tem", len(request.files), "arquivos!", request.form['size']
        if len(request.files) <= 0:
            return "Voc&ecirc; n&atilde;o enviou nenhum v&iacute;deo."
        try:
            f = request.files['fileToUpload']
            if allowed_file(f.filename):
                #print dir(f)
                filename = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                #Grava as informacoes adicionais em um arquivo texto
                file_infos = open("%s.txt" % os.path.join(app.config['UPLOAD_FOLDER'], filename)[:-4], 'w')
                file_infos.write("SIZE=%s" % request.form['size'])
                file_infos.close()
                #Trata o poster
                if len(request.files) > 1:
                    print "Saving poster"
                    poster_file = request.files['poster']
                    print poster_file.filename
                    pFileName = "poster_%s_%s" % (secure_filename(filename), secure_filename(poster_file.filename))
                    poster_file.save(os.path.join(app.config['UPLOAD_FOLDER'], pFileName))
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
def lista():
    arquivos = []
    for dirname, dirnames, filenames in os.walk(UPLOADED_FILES_DEST):
        for filename in filenames:
            #print os.path.join(dirname, filename)
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

if __name__ == "__main__":
    app.run(debug=True, port=APP_PORT, host=APP_HOST)
