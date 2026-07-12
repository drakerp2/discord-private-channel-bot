import asyncio
import json
import os

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

locks: dict[int, asyncio.Lock] = {}

bot = commands.Bot(command_prefix="private ", intents=intents, help_command=None)

config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs')
os.makedirs(config_dir, exist_ok=True)


@bot.command()
async def help(ctx: commands.Context[commands.Bot]):
    embed = discord.Embed(
        title="Bot Help Menu",
        description="Here is a list of available commands:",
        color=discord.Color.blue()
    )
    _ = embed.add_field(name="private create_member_channels", value="Initializes all private channels for the server.", inline=False)
    _ = embed.add_field(name="private add @Member|Role", value="Adds access to a member or role to every private channel current and future.", inline=False)
    _ = embed.add_field(name="private remove @Member|Role", value="Removes access to a member or role to every private channel current and future.", inline=False)
    _ = embed.add_field(name="private clear @Member|Role", value="Clears access to a member or role to every private channel current and future.", inline=False)
    _ = embed.add_field(name="On join behavior", value="Creates a new private channel for the member.", inline=False)

    
    await ctx.send(embed=embed)
pass



def get_permissions(guild: discord.Guild):
    guild_id = guild.id
    try:
        with open(f'{config_dir}/{guild_id}', 'r') as f:
            guild_config: dict[str,tuple[str,bool]] = json.load(f) # pyright: ignore[reportAny]
        pass
    except: return
    
    for id, val in guild_config.items():
        target_type, state = val
        if target_type == 'Member': 
            target = guild.get_member(int(id))
        else: 
            target = guild.get_role(int(id))
        pass

        if target is None: continue
        
        yield target, state 
    pass
pass

        





async def add_remove_clear_driver(ctx: commands.Context[commands.Bot], target: discord.Member|discord.Role, state: bool|None):
    if ctx.guild is None:
        _ = await ctx.send('command not supported here')
        return
    pass

    guild_id = ctx.guild.id
    if locks.get(guild_id) is None:
        locks[guild_id] = asyncio.Lock()
    pass

    async with locks[guild_id]:
        print(f'add remove clear {state} in {ctx.guild.name} for {target.name}')

        try:
            with open(f'{config_dir}/{guild_id}', 'r') as f:
                guild_config = json.load(f) # pyright: ignore[reportAny]
            pass
        except:
            guild_config = {}
        pass

        target_type = 'Member' if type(target) is discord.Member else 'Role'

        if state is not None: 
            guild_config[str(target.id)] = [target_type, state]
        else:
            guild_config.pop(str(target.id), None)
        pass


        try:
            with open(f'{config_dir}/{guild_id}', 'w') as f:
                json.dump(guild_config, f)
            pass
        except Exception as e:
            print(e)
            _ = await ctx.send('critical error occured during execution')
            return
        pass

        for channel in get_all_channels(ctx.guild):
            if state is not None:
                overwrites = channel.overwrites_for(target)
                overwrites.view_channel = state
            else:
                overwrites = None
            pass

            await channel.set_permissions(target, overwrite=overwrites)
        pass

        _ = await ctx.send('done')
        print('done')
pass

@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx: commands.Context[commands.Bot], target: discord.Member|discord.Role):
    await add_remove_clear_driver(ctx, target, True)
pass

@bot.command()
@commands.has_permissions(administrator=True)
async def remove(ctx: commands.Context[commands.Bot], target: discord.Member|discord.Role):
    await add_remove_clear_driver(ctx, target, False)
pass

@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx: commands.Context[commands.Bot], target: discord.Member|discord.Role):
    await add_remove_clear_driver(ctx, target, None)
pass



def get_channel_name(member: discord.Member):
    return f'{member.name}-private'.lower().replace(' ', '-')
pass

def get_all_channels(guild: discord.Guild):
    for i in range(1,501):
        category = discord.utils.get(guild.channels, name=f"private-channels-{i}")
        if category is None: continue
        if type(category) is not discord.CategoryChannel:
            print(f'channel "private-channels-{i}" is not a category')
            break
        pass
        
        for channel in category.channels: yield channel
    pass
pass
    

def get_all_channel_names(guild: discord.Guild):
    channel_names: list[str] = []
    
    for channel in get_all_channels(guild): channel_names.append(channel.name)

    return channel_names
pass


async def get_category(guild: discord.Guild, idx:int=1):
    category = discord.utils.get(guild.channels, name=f"private-channels-{idx}")

    if category is None:
        print(f'creating category "private-channels-{idx}')
        category = await guild.create_category(f'private-channels-{idx}') 
    pass

    if type(category) is not discord.CategoryChannel:
        print(f'channel "private-channels-{idx}" is not a category')
        return None
    pass

    return category
pass


@bot.event
async def on_member_join(member: discord.Member):
    id = member.guild.id
    if locks.get(id) is None:
        locks[id] = asyncio.Lock()
    pass
    async with locks[id]:
        print(f'member joined in {member.guild.name}')

        if get_channel_name(member) in get_all_channel_names(member.guild): 
            print(f'member {member.name} already has channel')
            return
        pass

        category = await get_category(member.guild)
        if category is None: return

        while len(category.channels) > 49:
            category = await get_category(member.guild, int(category.name.rsplit('-', 1)[1]) + 1)
            if category is None: return
        pass


        await create_channel(category, member)

        print('done')
    pass
pass



@bot.command()
@commands.has_permissions(administrator=True)
async def create_member_channels(ctx: commands.Context[commands.Bot]):
    if ctx.guild is None:
        print('guild cannot be none')
        return
    pass

    id = ctx.guild.id
    if locks.get(id) is None:
        locks[id] = asyncio.Lock()
    pass

    async with locks[id]:
        print(f'received create command from {ctx.guild.name}')


        category = await get_category(ctx.guild)
        if category is None: return

        member_list = ctx.guild.members

        channel_list = get_all_channel_names(ctx.guild) 


        for member in member_list:
            if member.bot: continue
            print(f'checking {member.name}')
            
            if get_channel_name(member) in channel_list: continue
            

            while len(category.channels) > 49:
                category = await get_category(ctx.guild, int(category.name.rsplit('-', 1)[1]) + 1)
                if category is None: return
            pass

            await create_channel(category, member)
            channel_list.append(get_channel_name(member))

        pass

        _ = await ctx.send('done')
        print('done')
    pass
pass


async def create_channel(category: discord.CategoryChannel, member:discord.Member):
    print(f'creating channel for {member.name} in {category.name} in {category.guild.name}')
    guild = category.guild

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),

        member: discord.PermissionOverwrite(view_channel=True),

        guild.me: discord.PermissionOverwrite(view_channel=True),
    }

    for target, state in get_permissions(guild):
        overwrites[target] = discord.PermissionOverwrite(view_channel=state)
    pass


    _ = await guild.create_text_channel(
        name=get_channel_name(member),
        overwrites=overwrites, # pyright: ignore[reportArgumentType]
        category=category
    )
    print('channel created')
pass


if __name__ == '__main__':
    with open('./token', 'r') as f:
        bot.run(f.read())

