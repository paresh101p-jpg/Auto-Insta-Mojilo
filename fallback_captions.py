import random

# =====================================================================
# MOJILOMART - Custom T-Shirt & DTF Sticker Fallback Captions
# 10 Openings × 15 Thoughts = 150+ unique combinations
# =====================================================================

OPENINGS = [
    "Apni pehchaan banao, Custom T-Shirt ke saath! 👕🔥",
    "Style toh custom mein hi hai yaar! 😎✨",
    "Teri T-shirt, teri kahani! Print karo jo dil chaahe! 💪🎨",
    "Boring T-shirts ko bol do bye-bye! 👋 Custom hai na! 🔥",
    "Jab design tum banao, toh look naturally unique hota hai! 👑🖨️",
    "Har kapda sirf kapda nahi hota — jab wo custom ho, toh wo ek expression banta hai! ✨",
    "Duniya mein milta hai, par tumhara style toh sirf tumhara! Custom karo! 🌟",
    "DTF Stickers se lekar Full Custom Prints tak — sab kuch Surat mein! 💥",
    "Custom printing ki duniya mein welcome! Jahan har design unique hota hai! 🎨🔥",
    "Naya look chahiye? Custom T-Shirt se shuru karo! Affordable + Stylish! 👕✨",
]

THOUGHTS = [
    "Custom T-shirts sirf kapde nahi hote — ye apni identity dikhane ka ek powerful tarika hain! Apna favourite quote, apna design, apna logo — sab kuch print karwa sakte ho MojiloMart ke saath! Surat mein best quality, best price! 💪🎨",
    "DTF Stickers ki baat karo toh MojiloMart ka koi jawab nahi! Har rang, har texture pe perfect print — bina fade kiye, bina crackle kiye. Apne business ke liye, apne family events ke liye ya phir sirf apne style ke liye — hum ready hain! 🔥✨",
    "Birthday gift dhoondh rahe ho kuch hatke? Ek personalized custom T-shirt se better kya hoga! Unka naam, unka favourite quote, ya unki photo — sab kuch print karwa do MojiloMart pe aur unka chehra dekhna mat bhoolna! 🎂😍",
    "Corporate events, team uniforms, farewell, wedding, college fests — har occasion ke liye custom bulk printing available hai MojiloMart mein! Best quality guarantee ke saath, fastest delivery ke saath. DM karo aaj hi! 💼👕",
    "Tumhare business ka logo hai? Branding ke liye custom T-shirts aur DTF stickers se bada koi affordable marketing tool nahi! Customers dekhenge, yaad rakhenge. MojiloMart — Surat ki #1 printing choice! 🚀🎯",
    "Ek simple T-shirt ke upar ek killer design — aur dekho kaise teri personality pop karti hai! MojiloMart mein tum apna khud ka design la sakte ho ya hum banayenge tumhare liye. Premium quality, budget-friendly price! 😎👕",
    "DTF (Direct-to-Film) printing technology ka matlab hai — ultra-vibrant colours, crystal clear details aur long-lasting prints jo dhone pe bhi fade nahi hote! Yahi reason hai ki log MojiloMart choose karte hain, baar baar! 🌈✨",
    "School ke bacchon ki sport jersey ho ya office ki formal branded shirts — MojiloMart har tarah ki bulk order ke liye ready hai! Fast turnaround time, premium fabric, aur guaranteed satisfaction — ye hain hamare promises! 🏆👕",
    "Khud ke liye custom T-shirt banana ekdum easy hai! Bas design bhejo, quantity batao, aur hum baaki sambhaale. No minimum order — single piece bhi print karein! MojiloMart — Surat ka sabse trustworthy printing partner! 💬🎨",
    "Apne pet ka photo, apni family ki pic, ya koi motivational quote — sab kuch kapde pe print ho sakta hai aur ekdum perfect lagta hai! Ye ho sakta hai MojiloMart ke DTF printing technology se! Try karo aaj! 📸👕",
    "Agar tum Surat mein ho aur custom printing ki zaroorat hai, toh seedha humse contact karo! Same-day printing bhi available hai urgent orders ke liye. Quality se zero compromise, price se zero drama! ✅🔥",
    "Event planner ho? Club organizer ho? Ya phir apna khud ka brand start karna chahte ho? MojiloMart tumhara perfect printing partner hai! Custom hoodies, custom caps, custom bags, custom stickers — sab kuch ek jagah! 🎽🎒",
    "Surat mein MojiloMart ke custom T-shirts itne popular kyu hain? Kyunki ye sirf print nahi karte — ye quality deliver karte hain! Har stitch, har colour accurate hai aur customer satisfaction guaranteed hai! 🌟💯",
    "Dosto ke saath matching outfits ka plan hai? Best friends ke liye twinning T-shirts chahiye? Ya couple goals ke liye matching hoodies? MojiloMart mein sab kuch possible hai, affordable price mein! 👫👕",
    "Ek custom T-shirt gift karo aur dekho unki khushi — kyunki koi bhi cheez uss feeling ko replace nahi kar sakti jab wo dekhte hain ki tumne unke liye kuch itna personal banwaya! MojiloMart — print memories, not just fabric! 💝🎁",
]

CTA = (
    "DM us for Custom T-Shirt Printing and DTF Stickers in Surat! 👕🔥\n"
    "Follow for more amazing designs! 👇\n"
    "Instagram: @MOJILOMART\n"
    "Facebook: @MojiloMart\n\n"
    "Like ❤️ | Comment 💬 | Share 🚀 | Save 📌\n\n"
    "#mojilo #mojilomart #tshirtprinting #dtfsticker #customtshirt #suratfashion "
    "#customprinting #surat #tshirtdesign #dtfprinting #brandedtshirts #bulkorder "
    "#corporategifts #personalisedgifts #suratbusiness #fashionprint #trending "
    "#customhoodies #suratprinting #printingservices"
)


def get_random_fallback_caption():
    opening = random.choice(OPENINGS)
    thought = random.choice(THOUGHTS)
    return f"{opening}\n\n{thought}\n\n{CTA}"


if __name__ == '__main__':
    print(get_random_fallback_caption())
