
import discord
from discord.ext import commands
import json
import os
from datetime import datetime

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Arquivo para armazenar dados
DATA_FILE = 'bot_data.json'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'users': {},
            'items': [],
            'purchases': []
        }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@bot.event
async def on_ready():
    print(f'{bot.user} está online!')

@bot.command(name='saldo')
async def saldo(ctx):
    data = load_data()
    user_id = str(ctx.author.id)
    
    if user_id not in data['users']:
        data['users'][user_id] = {'tokens': 0}
        save_data(data)
    
    tokens = data['users'][user_id]['tokens']
    embed = discord.Embed(
        title="💰 Seu Saldo",
        description=f"Você tem **{tokens}** tokens",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

@bot.command(name='loja')
async def loja(ctx):
    data = load_data()
    
    if not data['items']:
        embed = discord.Embed(
            title="🏪 Loja",
            description="A loja está vazia!",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(title="🏪 Loja", color=0x0099ff)
    
    for i, item in enumerate(data['items'], 1):
        embed.add_field(
            name=f"ID: {i} - {item['nome']}",
            value=f"Preço: {item['preco']} tokens\n{item['descricao']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='comprar')
async def comprar(ctx, item_id: int):
    data = load_data()
    user_id = str(ctx.author.id)
    
    if user_id not in data['users']:
        data['users'][user_id] = {'tokens': 0}
    
    if item_id < 1 or item_id > len(data['items']):
        await ctx.send("❌ ID do item inválido!")
        return
    
    item = data['items'][item_id - 1]
    user_tokens = data['users'][user_id]['tokens']
    
    if user_tokens < item['preco']:
        await ctx.send(f"❌ Você não tem tokens suficientes! Precisa de {item['preco']} tokens.")
        return
    
    # Realizar compra
    data['users'][user_id]['tokens'] -= item['preco']
    
    # Adicionar ao histórico
    purchase = {
        'usuario': ctx.author.name,
        'item': item['nome'],
        'preco': item['preco'],
        'data': datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    data['purchases'].append(purchase)
    
    save_data(data)
    
    embed = discord.Embed(
        title="✅ Compra Realizada!",
        description=f"Você comprou **{item['nome']}** por {item['preco']} tokens!",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

@bot.command(name='ranking')
async def ranking(ctx):
    data = load_data()
    
    if not data['users']:
        await ctx.send("❌ Nenhum usuário encontrado!")
        return
    
    # Ordenar usuários por tokens
    sorted_users = sorted(data['users'].items(), key=lambda x: x[1]['tokens'], reverse=True)
    
    embed = discord.Embed(title="🏆 Ranking de Tokens", color=0xffd700)
    
    for i, (user_id, user_data) in enumerate(sorted_users[:10], 1):
        try:
            user = await bot.fetch_user(int(user_id))
            embed.add_field(
                name=f"{i}º lugar",
                value=f"{user.name}: {user_data['tokens']} tokens",
                inline=False
            )
        except:
            continue
    
    await ctx.send(embed=embed)

@bot.command(name='historico')
async def historico(ctx):
    data = load_data()
    user_id = str(ctx.author.id)
    
    user_purchases = [p for p in data['purchases'] if p['usuario'] == ctx.author.name]
    
    if not user_purchases:
        await ctx.send("❌ Você ainda não fez nenhuma compra!")
        return
    
    embed = discord.Embed(title="📋 Seu Histórico de Compras", color=0x0099ff)
    
    for purchase in user_purchases[-10:]:  # Últimas 10 compras
        embed.add_field(
            name=purchase['item'],
            value=f"Preço: {purchase['preco']} tokens\nData: {purchase['data']}",
            inline=True
        )
    
    await ctx.send(embed=embed)

@bot.command(name='dar')
@commands.has_permissions(administrator=True)
async def dar(ctx, member: discord.Member, quantidade: int):
    data = load_data()
    user_id = str(member.id)
    
    if user_id not in data['users']:
        data['users'][user_id] = {'tokens': 0}
    
    data['users'][user_id]['tokens'] += quantidade
    save_data(data)
    
    embed = discord.Embed(
        title="✅ Tokens Dados!",
        description=f"{quantidade} tokens foram dados para {member.mention}",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

@bot.command(name='remover')
@commands.has_permissions(administrator=True)
async def remover(ctx, member: discord.Member, quantidade: int):
    data = load_data()
    user_id = str(member.id)
    
    if user_id not in data['users']:
        data['users'][user_id] = {'tokens': 0}
    
    # Não permitir que fique negativo
    if data['users'][user_id]['tokens'] < quantidade:
        await ctx.send(f"❌ {member.mention} só tem {data['users'][user_id]['tokens']} tokens!")
        return
    
    data['users'][user_id]['tokens'] -= quantidade
    save_data(data)
    
    embed = discord.Embed(
        title="✅ Tokens Removidos!",
        description=f"{quantidade} tokens foram removidos de {member.mention}",
        color=0xff9900
    )
    await ctx.send(embed=embed)

@bot.command(name='adicionar_item')
@commands.has_permissions(administrator=True)
async def adicionar_item(ctx, preco: int, *, nome_descricao):
    try:
        nome, descricao = nome_descricao.split(' | ', 1)
    except ValueError:
        await ctx.send("❌ Formato incorreto! Use: `!adicionar_item <preço> <nome> | <descrição>`")
        return
    
    data = load_data()
    
    item = {
        'nome': nome.strip(),
        'preco': preco,
        'descricao': descricao.strip()
    }
    
    data['items'].append(item)
    save_data(data)
    
    embed = discord.Embed(
        title="✅ Item Adicionado!",
        description=f"**{item['nome']}** foi adicionado à loja por {item['preco']} tokens",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

@dar.error
@remover.error
@adicionar_item.error
async def permission_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para usar este comando!")

# Iniciar o bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ Token do Discord não encontrado!")
        print("Adicione seu token na aba Secrets com a chave: DISCORD_TOKEN")
    else:
        bot.run(token)
