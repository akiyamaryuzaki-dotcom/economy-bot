import discord
from discord.ext import commands
import json
import os
import random
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
TOKEN = "YOUR_BOT_TOKEN_HERE"   # <-- paste your token
PREFIX = "+"
DATA_FILE = "economy_data.json"
WORK_COOLDOWN_MINUTES = 1       # minutes between +work uses

# ─────────────────────────────────────────────
#  JOB & EDUCATION DEFINITIONS
# ─────────────────────────────────────────────

JOBS = {
    "unemployed": {
        "tier": 0,
        "wage_min": 0, "wage_max": 0,
        "products": [],
        "description": "No job. Earn nothing."
    },
    "farmer": {
        "tier": 0,
        "wage_min": 10, "wage_max": 25,
        "products": ["wheat", "corn", "potato", "carrot"],
        "description": "Grows agricultural products."
    },
    "fisherman": {
        "tier": 0,
        "wage_min": 12, "wage_max": 28,
        "products": ["fish", "shrimp", "crab"],
        "description": "Catches seafood."
    },
    "miner": {
        "tier": 1,
        "wage_min": 30, "wage_max": 55,
        "products": ["iron_ore", "coal", "gold_ore"],
        "description": "Mines raw resources."
    },
    "craftsman": {
        "tier": 1,
        "wage_min": 35, "wage_max": 60,
        "products": ["wooden_plank", "brick", "rope"],
        "description": "Crafts basic goods."
    },
    "merchant": {
        "tier": 2,
        "wage_min": 60, "wage_max": 100,
        "products": ["trade_goods", "luxury_fabric", "spices"],
        "description": "Trades premium goods."
    },
    "engineer": {
        "tier": 2,
        "wage_min": 80, "wage_max": 130,
        "products": ["machine_part", "tool_kit", "blueprint"],
        "description": "Produces industrial parts."
    },
    "doctor": {
        "tier": 3,
        "wage_min": 150, "wage_max": 250,
        "products": ["medicine", "vaccine", "health_kit"],
        "description": "Provides medical supplies."
    },
    "banker": {
        "tier": 3,
        "wage_min": 200, "wage_max": 350,
        "products": ["bond", "investment_note", "financial_report"],
        "description": "Generates financial instruments."
    },
}

EDUCATION = [
    None,
    {"name": "High School Diploma", "cost": 200,  "emoji": "🏫"},
    {"name": "College Degree",      "cost": 800,  "emoji": "🎓"},
    {"name": "University Degree",   "cost": 2500, "emoji": "🏛️"},
]

PRODUCT_PRICES = {
    "wheat": 8,         "corn": 9,          "potato": 7,      "carrot": 10,
    "fish": 14,         "shrimp": 18,       "crab": 22,
    "iron_ore": 30,     "coal": 25,         "gold_ore": 55,
    "wooden_plank": 28, "brick": 32,        "rope": 20,
    "trade_goods": 65,  "luxury_fabric": 90,"spices": 85,
    "machine_part": 100,"tool_kit": 110,    "blueprint": 95,
    "medicine": 180,    "vaccine": 210,     "health_kit": 160,
    "bond": 250,        "investment_note": 300, "financial_report": 220,
}

PRODUCT_EMOJIS = {
    "wheat": "🌾",      "corn": "🌽",       "potato": "🥔",   "carrot": "🥕",
    "fish": "🐟",       "shrimp": "🍤",     "crab": "🦀",
    "iron_ore": "⛏️",   "coal": "🪨",       "gold_ore": "🥇",
    "wooden_plank": "🪵","brick": "🧱",     "rope": "🪢",
    "trade_goods": "📦","luxury_fabric": "🧣","spices": "🫙",
    "machine_part": "⚙️","tool_kit": "🔧",  "blueprint": "📐",
    "medicine": "💊",   "vaccine": "💉",    "health_kit": "🩺",
    "bond": "📜",       "investment_note": "💹","financial_report": "📊",
}

# ─────────────────────────────────────────────
#  DATA HELPERS
# ─────────────────────────────────────────────

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "shop": {}, "gdp": 0.0}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user(data, user_id: str):
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "balance": 100.0,
            "job": "unemployed",
            "education_tier": 0,
            "inventory": {},
            "last_work": None,
            "total_earned": 0.0,
        }
    return data["users"][user_id]

# ─────────────────────────────────────────────
#  BOT SETUP
# ─────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ─────────────────────────────────────────────
#  EVENTS
# ─────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅  {bot.user} is online!")

# ─────────────────────────────────────────────
#  COMMANDS
# ─────────────────────────────────────────────

# ── BALANCE ──────────────────────────────────
@bot.command(name="balance", aliases=["bal", "wallet"])
async def balance(ctx):
    data = load_data()
    u = get_user(data, str(ctx.author.id))
    save_data(data)
    edu_name = EDUCATION[u["education_tier"]]["name"] if u["education_tier"] > 0 else "None"

    embed = discord.Embed(title=f"💰 {ctx.author.display_name}'s Wallet", color=0xf5c518)
    embed.add_field(name="Balance",      value=f"**${u['balance']:,.2f}**",   inline=True)
    embed.add_field(name="Job",          value=f"**{u['job'].title()}**",      inline=True)
    embed.add_field(name="Education",    value=edu_name,                       inline=True)
    embed.add_field(name="Total Earned", value=f"${u['total_earned']:,.2f}",   inline=True)
    await ctx.send(embed=embed)

# ── WORK ─────────────────────────────────────
@bot.command(name="work")
async def work(ctx):
    data = load_data()
    u = get_user(data, str(ctx.author.id))

    if u["job"] == "unemployed":
        await ctx.send("❌ You don't have a job! Use `+getjob <job>` to get one.")
        save_data(data)
        return

    now = datetime.utcnow()
    if u["last_work"]:
        last = datetime.fromisoformat(u["last_work"])
        diff = now - last
        if diff < timedelta(minutes=WORK_COOLDOWN_MINUTES):
            remaining = timedelta(minutes=WORK_COOLDOWN_MINUTES) - diff
            mins = int(remaining.total_seconds() // 60)
            secs = int(remaining.total_seconds() % 60)
            await ctx.send(f"⏳ You need to rest! Work again in **{mins}m {secs}s**.")
            save_data(data)
            return

    job_info = JOBS[u["job"]]
    wage = random.randint(job_info["wage_min"], job_info["wage_max"])
    product = random.choice(job_info["products"])
    qty = random.randint(1, 4)
    sell_value = PRODUCT_PRICES[product] * qty
    total_income = wage + sell_value

    if product not in data["shop"]:
        data["shop"][product] = 0
    data["shop"][product] += qty

    u["balance"] += total_income
    u["total_earned"] += total_income
    u["last_work"] = now.isoformat()
    data["gdp"] += total_income

    save_data(data)

    emoji = PRODUCT_EMOJIS.get(product, "📦")
    embed = discord.Embed(
        title=f"🔨 {ctx.author.display_name} worked as {u['job'].title()}!",
        color=0x2ecc71
    )
    embed.add_field(name="Wage",         value=f"${wage}",                                              inline=True)
    embed.add_field(name="Product Sold", value=f"{emoji} {qty}x {product.replace('_',' ').title()} → ${sell_value}", inline=True)
    embed.add_field(name="Total Earned", value=f"💵 **+${total_income}**",                              inline=False)
    embed.add_field(name="New Balance",  value=f"${u['balance']:,.2f}",                                 inline=True)
    embed.set_footer(text=f"Products added to shop • Work again in {WORK_COOLDOWN_MINUTES}m")
    await ctx.send(embed=embed)

# ── JOBS ─────────────────────────────────────
@bot.command(name="jobs")
async def jobs_list(ctx):
    data = load_data()
    u = get_user(data, str(ctx.author.id))
    save_data(data)

    tier_labels = ["No Education", "High School", "College", "University"]
    embed = discord.Embed(title="💼 Available Jobs", color=0x3498db)
    embed.description = f"Your education tier: **{tier_labels[u['education_tier']]}**\n\n"

    for jname, jinfo in JOBS.items():
        if jname == "unemployed":
            continue
        req = tier_labels[jinfo["tier"]]
        locked = "🔒" if jinfo["tier"] > u["education_tier"] else "✅"
        wage_range = f"${jinfo['wage_min']}–${jinfo['wage_max']}/work"
        prods = ", ".join(p.replace("_", " ").title() for p in jinfo["products"])
        embed.add_field(
            name=f"{locked} {jname.title()} (requires {req})",
            value=f"💵 {wage_range}\n📦 Produces: {prods}\n_{jinfo['description']}_",
            inline=False
        )
    embed.set_footer(text="Use +getjob <jobname> to apply | +education to study")
    await ctx.send(embed=embed)

# ── GET JOB ───────────────────────────────────
@bot.command(name="getjob")
async def get_job(ctx, *, job_name: str):
    data = load_data()
    u = get_user(data, str(ctx.author.id))
    job_name = job_name.lower().strip()

    if job_name not in JOBS or job_name == "unemployed":
        await ctx.send(f"❌ Unknown job `{job_name}`. Use `+jobs` to see available jobs.")
        save_data(data)
        return

    jinfo = JOBS[job_name]
    if jinfo["tier"] > u["education_tier"]:
        needed = EDUCATION[jinfo["tier"]]["name"]
        await ctx.send(f"❌ You need a **{needed}** to become a {job_name.title()}. Use `+education` to enroll.")
        save_data(data)
        return

    u["job"] = job_name
    save_data(data)
    await ctx.send(f"✅ You are now a **{job_name.title()}**! Use `+work` to start earning.")

# ── EDUCATION ────────────────────────────────
@bot.command(name="education", aliases=["edu", "school"])
async def education(ctx):
    data = load_data()
    u = get_user(data, str(ctx.author.id))
    save_data(data)

    embed = discord.Embed(title="🎓 Education System", color=0x9b59b6)
    embed.description = "Higher education unlocks better-paying jobs.\n\n"

    for tier, edu in enumerate(EDUCATION):
        if edu is None:
            embed.add_field(name="Tier 0 – No Education", value="Everyone starts here. Access: Farmer, Fisherman.", inline=False)
            continue
        status = "✅ Completed" if u["education_tier"] >= tier else f"${edu['cost']} — `+enroll tier{tier}`"
        jobs_unlocked = [j for j, info in JOBS.items() if info["tier"] == tier]
        embed.add_field(
            name=f"{edu['emoji']} Tier {tier} – {edu['name']}",
            value=f"**Cost:** {status}\n**Unlocks:** {', '.join(j.title() for j in jobs_unlocked)}",
            inline=False
        )
    await ctx.send(embed=embed)

# ── ENROLL ───────────────────────────────────
@bot.command(name="enroll")
async def enroll(ctx, tier_str: str):
    data = load_data()
    u = get_user(data, str(ctx.author.id))

    try:
        tier = int(tier_str.replace("tier", "").strip())
    except ValueError:
        await ctx.send("❌ Usage: `+enroll tier1` / `+enroll tier2` / `+enroll tier3`")
        save_data(data)
        return

    if tier < 1 or tier >= len(EDUCATION):
        await ctx.send("❌ Invalid tier. Valid tiers: 1, 2, 3.")
        save_data(data)
        return

    if u["education_tier"] >= tier:
        await ctx.send("✅ You already have this education level or higher!")
        save_data(data)
        return

    if u["education_tier"] < tier - 1:
        prev = EDUCATION[tier - 1]["name"]
        await ctx.send(f"❌ You must complete **{prev}** first!")
        save_data(data)
        return

    edu = EDUCATION[tier]
    cost = edu["cost"]
    if u["balance"] < cost:
        await ctx.send(f"❌ You need **${cost}** to enroll in {edu['name']}. You have ${u['balance']:,.2f}.")
        save_data(data)
        return

    u["balance"] -= cost
    u["education_tier"] = tier
    save_data(data)

    await ctx.send(
        f"🎓 Congratulations! You earned your **{edu['name']}** {edu['emoji']}!\n"
        f"💸 Paid **${cost}** | Balance: **${u['balance']:,.2f}**\n"
        f"Use `+jobs` to see newly unlocked jobs!"
    )

# ── SHOP ─────────────────────────────────────
@bot.command(name="shop")
async def shop(ctx):
    data = load_data()
    shop_stock = {k: v for k, v in data["shop"].items() if v > 0}

    embed = discord.Embed(title="🏪 Player-Stocked Shop", color=0xe67e22)

    if not shop_stock:
        embed.description = "⚠️ The shop is empty! Workers need to `+work` to stock it."
    else:
        embed.description = "All items here were produced by workers. Buy with `+buy <item> <qty>`.\n\n"
        for product, qty in sorted(shop_stock.items()):
            emoji = PRODUCT_EMOJIS.get(product, "📦")
            price = PRODUCT_PRICES[product]
            embed.add_field(
                name=f"{emoji} {product.replace('_',' ').title()}",
                value=f"Stock: **{qty}** | Price: **${price}** each",
                inline=True
            )

    embed.set_footer(text="Prices are set by the economy • Stock depends on workers!")
    await ctx.send(embed=embed)

# ── BUY ──────────────────────────────────────
@bot.command(name="buy")
async def buy(ctx, item: str, qty: int = 1):
    data = load_data()
    u = get_user(data, str(ctx.author.id))
    item = item.lower().replace("-", "_").replace(" ", "_")

    if item not in data["shop"] or data["shop"][item] < qty:
        available = data["shop"].get(item, 0)
        await ctx.send(f"❌ Not enough `{item}` in stock. Available: {available}.")
        save_data(data)
        return

    price = PRODUCT_PRICES.get(item)
    if not price:
        await ctx.send("❌ Unknown item.")
        save_data(data)
        return

    total_cost = price * qty
    if u["balance"] < total_cost:
        await ctx.send(f"❌ You need **${total_cost}** but only have **${u['balance']:,.2f}**.")
        save_data(data)
        return

    u["balance"] -= total_cost
    data["shop"][item] -= qty
    if item not in u["inventory"]:
        u["inventory"][item] = 0
    u["inventory"][item] += qty

    save_data(data)
    emoji = PRODUCT_EMOJIS.get(item, "📦")
    await ctx.send(
        f"✅ Bought **{qty}x {emoji} {item.replace('_',' ').title()}** for **${total_cost}**.\n"
        f"Balance: **${u['balance']:,.2f}**"
    )

# ── INVENTORY ────────────────────────────────
@bot.command(name="inventory", aliases=["inv"])
async def inventory(ctx):
    data = load_data()
    u = get_user(data, str(ctx.author.id))
    save_data(data)

    inv = {k: v for k, v in u["inventory"].items() if v > 0}
    embed = discord.Embed(title=f"🎒 {ctx.author.display_name}'s Inventory", color=0x1abc9c)
    if not inv:
        embed.description = "Your inventory is empty."
    else:
        for item, qty in inv.items():
            emoji = PRODUCT_EMOJIS.get(item, "📦")
            embed.add_field(name=f"{emoji} {item.replace('_',' ').title()}", value=f"x{qty}", inline=True)
    await ctx.send(embed=embed)

# ── GDP ───────────────────────────────────────
@bot.command(name="gdp")
async def gdp(ctx):
    data = load_data()
    guild = ctx.guild
    player_count = sum(1 for m in guild.members if not m.bot)
    total_gdp = data.get("gdp", 0.0)
    gdp_per_capita = total_gdp / player_count if player_count > 0 else 0
    total_money = sum(u["balance"] for u in data["users"].values())
    total_shop_value = sum(PRODUCT_PRICES.get(p, 0) * qty for p, qty in data["shop"].items())

    embed = discord.Embed(title="📊 Server Economy — GDP Report", color=0xf39c12)
    embed.add_field(name="🌐 Total GDP",            value=f"**${total_gdp:,.2f}**",       inline=True)
    embed.add_field(name="👤 GDP per Capita",       value=f"**${gdp_per_capita:,.2f}**",   inline=True)
    embed.add_field(name="👥 Players (non-bot)",    value=f"**{player_count}**",            inline=True)
    embed.add_field(name="💵 Money in Circulation", value=f"${total_money:,.2f}",           inline=True)
    embed.add_field(name="🏪 Shop Inventory Value", value=f"${total_shop_value:,.2f}",      inline=True)
    embed.set_footer(text="GDP = total currency generated by all work activity")
    await ctx.send(embed=embed)

# ── LEADERBOARD ───────────────────────────────
@bot.command(name="leaderboard", aliases=["top", "lb"])
async def leaderboard(ctx):
    data = load_data()
    guild = ctx.guild
    entries = []
    for uid, u in data["users"].items():
        member = guild.get_member(int(uid))
        if member and not member.bot:
            entries.append((member.display_name, u["balance"], u["job"]))

    entries.sort(key=lambda x: x[1], reverse=True)

    embed = discord.Embed(title="🏆 Richest Players", color=0xf1c40f)
    medals = ["🥇", "🥈", "🥉"]
    for i, (name, bal, job) in enumerate(entries[:10]):
        medal = medals[i] if i < 3 else f"#{i+1}"
        embed.add_field(
            name=f"{medal} {name}",
            value=f"${bal:,.2f} · {job.title()}",
            inline=False
        )
    await ctx.send(embed=embed)

# ── HELP ──────────────────────────────────────
@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="📖 Economy Bot — Commands", color=0x2c3e50)
    embed.add_field(name="💰 Economy",
        value=(
            "`+balance` — View your balance & job\n"
            "`+work` — Work & produce goods (1m cooldown)\n"
            "`+leaderboard` — Top 10 richest players\n"
            "`+gdp` — Server GDP & GDP per capita"
        ), inline=False)
    embed.add_field(name="💼 Jobs",
        value=(
            "`+jobs` — List all jobs & requirements\n"
            "`+getjob <jobname>` — Apply for a job"
        ), inline=False)
    embed.add_field(name="🎓 Education",
        value=(
            "`+education` — View education tiers & costs\n"
            "`+enroll tier1/2/3` — Enroll & pay for a degree"
        ), inline=False)
    embed.add_field(name="🏪 Shop",
        value=(
            "`+shop` — Browse player-stocked items\n"
            "`+buy <item> <qty>` — Purchase items\n"
            "`+inventory` — View your items"
        ), inline=False)
    embed.set_footer(text="Economy powered by player work • All stock comes from workers!")
    await ctx.send(embed=embed)

# ─────────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────────
import os
bot.run(os.getenv("TOKEN"))