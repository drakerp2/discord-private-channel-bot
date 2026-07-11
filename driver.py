import asyncio

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

locks: dict[int, asyncio.Lock] = {}

bot = commands.Bot(command_prefix="!", intents=intents)

def get_channel_name(member: discord.Member):
    return f'{member.name}-private'.lower().replace(' ', '-')
pass

def get_all_channel_names(guild: discord.Guild):
    channel_names: list[str] = []
    
    for i in range(1,501):
        category = discord.utils.get(guild.channels, name=f"private-channels-{i}")
        if category is None: continue
        if type(category) is not discord.CategoryChannel:
            print(f'channel "private-channels-{i}" is not a category')
            break
        pass
        
        for channel in category.channels: channel_names.append(channel.name)
    pass

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
    print(f'member joined in {member.guild.name}')
    id = member.guild.id
    if locks.get(id) is None:
        locks[id] = asyncio.Lock()
    pass
    async with locks[id]:
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
    pass
pass



@bot.command()
async def create_member_channels(ctx: commands.Context[commands.Bot]):
    if ctx.guild is None:
        print('guild cannot be none')
        return
    pass

    print(f'received create command from {ctx.guild.name}')

    id = ctx.guild.id
    if locks.get(id) is None:
        locks[id] = asyncio.Lock()
    pass
    async with locks[id]:
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

