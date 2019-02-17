
from flask import render_template
from app import app, db



from app.models.forms import CadastroForm

from app.models.tables import Imovel
#from app.models.tables import User

#CONFIGURAÇÃO DA ROTA DE INDEX
@app.route("/index/")
@app.route("/")
def index():
	#RENDERIZAÇÃO DO TEMPLATE DA TELA PRINCIPAL
	return render_template('index.html')


#CONFIGURAÇÃO DA ROTA DE CADASTRO
@app.route("/cadastro/")
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
	#Recebendo o valor dos dados vindos da classe CadastroForm
	form = CadastroForm()
	#Se o submit for validado, então:
	if form.validate_on_submit():
		print("A matricula é: " + form.matricula.data)
		print("O Tipo do imóvel é: "+ form.tipoImovel.data)
		print("A opção escolhida foi: "+ form.areaImovel.data)
		print("O enderecoUser é: " + form.enderecoUser.data)
		print("A latitude do user é: "+ form.latUser.data)
		print("A longitude do user é : "+form.longUser.data)



		cadastrar = Imovel(matricula=form.matricula.data,tipoImovel= form.tipoImovel.data, areaImovel=form.areaImovel.data,enderecoUser=form.enderecoUser.data, latUser= form.latUser.data,longUser= form.longUser.data)
		db.session.add(cadastrar)
		db.session.commit()
		return "Cadastrado!"
		
		

	else:
		print(form.errors)

	#RENDERIZAÇÃO DO TEMPLATE PROJETO.HTML
	return render_template('projeto.html', form = form)
		



@app.route("/teste/<info>")
@app.route("/teste", defaults={"info":None})
def teste(info):
	
	#r = User.query.filter_by(username="Pedro").first()
	
	#i = User("Pedro", "1234", "Pedro", "pedro@gmail.com")
	#db.session.add(i)
	#db.session.commit()
	print (r.username, r.name)
	return "Ok"