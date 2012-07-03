Para utilizar o virtualenv:

$ virtualenv --no-site-packages env 

Se quiser apontar o virtualenv para um binário do python específico, utilize o parâmetro '-p'

$ virtualenv --no-site-packages env -p /usr/bin/python2

Ative o virtualenv

$ surce env/bin/activate

Agora instale os pre-requisitos:

$ pip install flask
$ pip install flask-uploads
$ pip install flask-login

Então edite o arquivo 'user_list.py' , edite a tupla USUARIOS conforme existe no exemplo, e edite/insira os usuarios e suas senhas de acesso.

Agora renomeie o arquivo conf.py.example para conf.py e edite-o com suas configuracoes desejadas, ou então deixe sem e use as configs padrão.

E para executar:
$ python upvideos.py

