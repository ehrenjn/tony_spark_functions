#A file containing all of wak's functions for tony spark
#Might be broken into a bunch of files if the bot gets bloated

import requests
import random
import re
import discord
import asyncio
import json


class JSONStore:
        
    def __init__(self, file_name):
        self._file = file_name
        try:
            with open(file_name, 'r') as f:
                self._store = json.loads(f.read())
        except FileNotFoundError:
            self._store = dict()
        
    def __setitem__(self, key, value):
        if not type(key) == str:
            raise Exception('Sorry, JSON can only store string keys')
        self._store[key] = value
        self.update()
            
    def __getitem__(self, key):
        return self._store.get(key)

    def update(self):
        '''updates the contents of the json file
            called when setting an item via __setitem__
            useful when storing mutable objects, ie:
            store['list'].append('item'); store.update()'''
        with open(self._file, 'w') as f:
            f.write(json.dumps(self._store))


STORAGE_FILE = 'wak_storage.json'

class WakStore(JSONStore):
    def __init__(self):
        super().__init__(STORAGE_FILE)
        if self['playables'] is None: #init playables so I don't have to keep checking if they're None
            self['playables'] = []
        

def setup(bot):

    storage = WakStore()

    @bot.command(name = "eval")
    async def execute(ctx, *, cmd): #if cmd arg is keyword only it lets discordpy know to pass in args as one string
        import random #import locally because I don't want eval to have global namespace
        import math
        import re
        try:
            return_val = str(eval(cmd, locals())) #only executes expressions, not statements.
            #ALSO: FOR SOME UNGODLY REASON eval WILL NOT CONSERVE locals IF YOU HAVE NESTED SCOPE
            #ie, eval("[math.sin(x) for x in range(10)]", None, locals()) WILL FAIL BECAUSE WHEN YOU DO LIST COMPREHENSION YOU CREATE A NESTED SCOPE, AND FOR SOME REASON THAT NESTED SCOPE IS EMPTY. IT DOESN'T CONTAIN locals
            #BUT NOTICE THAT THIS WILL ONLY BREAK FOR LOCAL SCOPE. SO ALL YOUR VARIABLES HAVE TO BE DEFINED IN GLOBAL SCOPE
            #THAT'S WHY IM PASSING IN locals() WHERE IM SUPPOSED TO BE PASSING IN globals()!!!!!!
            #ALSO BE AWARE THAT WHEN YOU USE eval OUTSIDE OF A FUNCTION AND DON'T SPECIFY ANY SCOPE PARAMS IT'LL USE THE CORRECT LOCAL AND GLOBAL SCOPES BY DEFAULT, AND LOCAL SCOPE WILL BE EQUAL TO GLOBAL SCOPE SO IT'LL ALL WORK OUT
            #THIS MEANS THAT I ALSO COULD HAVE IMPORTED THE MODULES OUTSIDE OF THE FUNCTION AND PASSED NO PARAMS INTO eval, HOWEVER THEN ALL MY GLOBALS WOULD BE AVAILABLE IN THE CALL TO eval WHICH WOULD BE A BIT OF A MESS
        except BaseException as e:
            return_val =  "{}: {}".format(e.__class__.__name__, e)
        if len(return_val) > 2000:
            await ctx.send("Sorry, the return value's too long to send")
        else:
            await ctx.send(return_val)

    @bot.command()
    async def img(ctx, *args):
        query = '+'.join(args) + '&source=lnms&tbm=isch'
        url = 'https://www.google.ca/search?q=' + query
        data = requests.get(url).content.decode(errors = 'ignore')
        imgs = re.findall(r'src="(https://encrypted-tbn0\.gstatic\.com/images.+?)"', data)
        if len(imgs) == 0:
            await ctx.send('No images found')
        else:
            embed = discord.Embed()
            embed.set_image(url = random.choice(imgs))
            await ctx.send(embed = embed)

    @bot.command()
    async def play(ctx, *, cmd):
        storage['playables'].append(cmd)
        storage.update()
        await bot.change_presence(game = discord.Game(name = cmd))
        await ctx.send('added playable')


    async def play_random_playable():
        playables = storage['playables']
        if len(playables) > 0:
            new_game = discord.Game(name = random.choice(playables))
            await bot.change_presence(game = new_game)
        else:
            await bot.change_presence(game = None)

    @bot.command()
    async def unplay(ctx, *, cmd):
        playables = storage['playables']
        if cmd in playables:
            playables.remove(cmd)
            storage.update()
            if ctx.guild is not None and ctx.guild.me.game.name not in playables: #ctx.guild is None if in DMs
                await play_random_playable()
            await ctx.send("removed playable")
        else:
            await ctx.send("Couldn't find playable: " + cmd)

    async def background():
        print('wak background process started')
        while bot.ws is None: #wait until ws connection is made (there is a short period of time after bot.run is called during which the event loop has started but a discord websocket hasn't been established)
            await asyncio.sleep(1)
        while True:
            await play_random_playable()
            await asyncio.sleep(int((random.random()+0.2)*30*60)) #add 0.2 so minimal time isn't 0
    bot.loop.create_task(background())
    
