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
     render_template, abort, flash, jsonify, send_from_directory
from flaskext.uploads import UploadSet
import sys
import os
import time
from stat import *
from werkzeug import secure_filename

#---------------------------------------------------------------------
UPLOADED_FILES_DEST = '/home/berlotto/Desenvolvimento/upvideos/uploads/'
UPLOADED_FILES_ALLOW = set(['ogg', 'ogv', 'webm', 'mp4'])
UPLOADED_FILES_DENY = ''
#---------------------------------------------------------------------

try:
    from conf import *
except:
    pass

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOADED_FILES_DEST

UPLOADED_FILES_ALLOW = ('ogg', 'ogv', 'webm', 'mp4')
videos = UploadSet('videos', UPLOADED_FILES_ALLOW)

#---------------------------------------------------------------------


def allowed_file(filename):
    '''
    Verify the allowed file extensions
    '''
    print "Verifiing %s " % filename
    return '.' in filename and filename.rsplit('.', 1)[1] in UPLOADED_FILES_ALLOW

#---------------------------------------------------------------------


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    #print "Uploading..."
    if request.method == 'POST':
        #print "Tem", len(request.files), "arquivos!"
        if len(request.files) <= 0:
            return "Voc&ecirc; n&atilde;o enviou nenhum v&iacute;deo."
        try:
            f = request.files['fileToUpload']
            if allowed_file(f.filename):
                #print dir(f)
                filename = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                #print 'filename=', filename
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


def getSize(size):
    if (size > 1024 * 1024):
        bytesTransfered = str(round(size * 100 / (1024 * 1024)) / 100) + 'MB'
    elif(size > 1024):
        bytesTransfered = str(round(size * 100 / 1024) / 100) + 'KB'
    else:
        bytesTransfered = str(round(size * 100) / 100) + 'Bytes'
    return bytesTransfered


@app.route('/lista-videos')
def lista():
    arquivos = []
    for dirname, dirnames, filenames in os.walk(UPLOADED_FILES_DEST):
        for filename in filenames:
            #print os.path.join(dirname, filename)
            st = os.stat(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            arquivos.append({'filename': filename, 'size': getSize(st[ST_SIZE]),
                             'date': time.asctime(time.localtime(st[ST_MTIME]))})
    return render_template('fileitem.html', files=arquivos)


@app.route('/v/<filename>')
def show(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/play/<filename>')
def player(filename):
    return render_template('play.html', filename=filename)


@app.route('/snippet/<filename>')
def snippet(filename):
    return render_template('snippet.html', filename=filename)

if __name__ == "__main__":
    app.run(debug=True, port=8000, host='0.0.0.0')
