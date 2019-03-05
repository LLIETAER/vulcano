from vulcano.app.classes import VulcanoApp
from vulcano.app.lexer import dark_theme


app = VulcanoApp()

@app.command("hi", "Salute people given form parameter")
def salute_method_here(name, title="Mr."):
    print("Hi! {} {} :) Glad to see you.".format(title, name))

@app.command()
def i_am(name):
    app.context['name'] = name

@app.command()
def whoami():
    print app.context['name']

@app.command()
def bye(name="User"):
    """ Say goodbye to someone """
    print("Bye {}!".format(name))


if __name__ == '__main__':
    app.run(theme=dark_theme)
