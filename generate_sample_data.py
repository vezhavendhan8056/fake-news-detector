# -*- coding: utf-8 -*-
# =============================================================================
# generate_sample_data.py — Generate Sample Dataset for Demo
# Run this if you don't have the Kaggle Fake.csv / True.csv dataset.
# This creates a small synthetic dataset so the app can be demonstrated.
# NOTE: For production/accurate results, use the real Kaggle dataset.
# =============================================================================

import os
import pandas as pd
import random

random.seed(42)

# ---------------------------------------------------------------------------
# Sample real news headlines + texts
# ---------------------------------------------------------------------------
REAL_NEWS = [
    {
        "title": "NASA Scientists Confirm Water Ice on Moon's Surface",
        "text": "Scientists at NASA have confirmed the presence of water ice on the moon's surface using data from the Lunar Reconnaissance Orbiter. The findings, published in the journal Nature Astronomy, show that water ice is concentrated at the lunar poles in permanently shadowed regions. This discovery could have significant implications for future moon missions and the possibility of establishing a permanent human presence on the moon. The water ice could potentially be used for drinking water or converted to hydrogen fuel for spacecraft. Mission planners at NASA say this discovery will influence their Artemis program, which aims to return humans to the moon by 2025. The research team used ultraviolet spectroscopy to identify the signature of water ice molecules on the surface."
    },
    {
        "title": "Federal Reserve Raises Interest Rates by Quarter Point",
        "text": "The Federal Reserve raised its benchmark interest rate by a quarter percentage point on Wednesday, continuing its campaign to bring inflation down to its 2 percent target. The decision, which was unanimous among voting members of the Federal Open Market Committee, brings the federal funds rate to a range of 5.25 to 5.5 percent, the highest level in 22 years. Fed Chairman Jerome Powell said at a news conference that the central bank remains committed to bringing inflation down but acknowledged that the economy has shown unexpected resilience. The latest economic data showed inflation at 3.2 percent annually, down from a peak of 9.1 percent in June 2022. Powell indicated that future rate decisions would depend on incoming economic data."
    },
    {
        "title": "World Health Organization Declares End to COVID-19 Emergency",
        "text": "The World Health Organization declared an end to the COVID-19 public health emergency of international concern on Thursday, marking a symbolic turning point in the pandemic that has killed millions worldwide. WHO Director-General Tedros Adhanom Ghebreyesus announced the decision at a press briefing in Geneva, saying the virus has evolved and the world has evolved. However, he warned that the virus was not finished and called on countries to maintain surveillance systems. The emergency declaration, which was first made in January 2020, had given WHO extraordinary powers to coordinate the global response to the pandemic. More than 765 million cases and nearly 7 million deaths have been officially reported to WHO since the beginning of the pandemic."
    },
    {
        "title": "Scientists Develop New Battery Technology That Charges in Minutes",
        "text": "Researchers at Stanford University have developed a new battery technology that can charge electric vehicles in just five minutes while maintaining energy capacity over thousands of charge cycles. The breakthrough, published in the journal Science, uses a novel aluminum-ion battery design that overcomes limitations of traditional lithium-ion batteries. Professor Hongjie Dai, who led the research team, said the new battery could fundamentally change the way we think about energy storage. The technology is still in the laboratory stage and would require significant investment to commercialize. However, experts say it could eventually reduce charging times from the current average of 30 minutes to just five minutes. The batteries also showed no degradation after 7,500 charge cycles in laboratory tests."
    },
    {
        "title": "Global Carbon Emissions Reach Record High Despite Climate Pledges",
        "text": "Global carbon dioxide emissions from fossil fuels reached a new record high in the current year, according to a report by the Global Carbon Project published on Tuesday. The report found that emissions increased by 1.1 percent compared to the previous year, driven mainly by growth in coal consumption in Asia and a recovery in air travel. Total emissions are estimated at 37.4 billion tonnes of carbon dioxide. Scientists said the findings highlight the gap between government climate pledges and actual progress in reducing emissions. The Intergovernmental Panel on Climate Change has warned that global emissions need to fall by about 43 percent by 2030 to limit warming to 1.5 degrees Celsius above pre-industrial levels."
    },
    {
        "title": "Supreme Court Rules on Landmark Social Media Regulation Case",
        "text": "The United States Supreme Court issued a landmark ruling on Thursday regarding state laws that attempted to regulate how social media companies moderate content on their platforms. In a unanimous decision, the court vacated lower court rulings that had blocked laws passed by Florida and Texas, which sought to prevent social media companies from removing or demoting content based on political viewpoints. The justices sent the cases back to the lower courts for further review, asking them to apply the First Amendment analysis outlined in their opinion. Legal experts said the ruling would have significant implications for how social media platforms operate and the extent to which they can be regulated by state governments."
    },
    {
        "title": "Electric Vehicle Sales Surpass 10 Million Units Worldwide",
        "text": "Global electric vehicle sales exceeded 10 million units for the first time in a single year, according to data released by the International Energy Agency. The milestone represents a 35 percent increase compared to the previous year and means that roughly one in seven cars sold globally was an electric vehicle. China remained the largest market, accounting for 60 percent of global EV sales, followed by Europe and the United States. The IEA report noted that the growth was supported by expanding charging infrastructure, government incentives, and an increasing number of affordable electric vehicle models. Battery prices have fallen more than 90 percent over the past decade, making electric vehicles increasingly competitive with conventional vehicles on purchase price."
    },
    {
        "title": "Breakthrough in Alzheimer's Treatment Shows Promise in Clinical Trials",
        "text": "A new drug candidate for treating Alzheimer's disease has shown significant promise in late-stage clinical trials, potentially offering hope to millions of patients worldwide. The drug, developed by Biogen in collaboration with Japanese pharmaceutical company Eisai, slowed cognitive decline by 27 percent compared to placebo in a trial involving nearly 1,800 patients. The trial results were presented at the Alzheimer's Association International Conference in Amsterdam. If approved by the Food and Drug Administration, the drug would be one of the first to directly target amyloid plaques in the brain, which are thought to play a key role in the development of Alzheimer's disease. Critics noted that the modest benefits would need to be weighed against potential side effects."
    },
    {
        "title": "International Space Station Receives New Solar Arrays from SpaceX Mission",
        "text": "A SpaceX Dragon cargo spacecraft successfully delivered new solar arrays to the International Space Station as part of a commercial resupply mission. The arrays, called iROSA (ISS Roll-Out Solar Arrays), will boost the station's power generation capacity by approximately 30 kilowatts. Astronauts aboard the ISS will perform spacewalks over the coming weeks to install the new arrays on existing truss segments. NASA officials said the upgraded power system will support future space exploration activities and maintain the station's operations through 2030. The mission also delivered scientific experiments, crew supplies, and equipment for ongoing research programs aboard the station. SpaceX has now completed more than 25 cargo resupply missions to the ISS under its Commercial Resupply Services contract with NASA."
    },
    {
        "title": "United Nations Climate Summit Produces New Emissions Reduction Agreement",
        "text": "World leaders at the United Nations Climate Change Conference reached a new agreement on reducing greenhouse gas emissions, committing major economies to phase out unabated coal power and accelerate the transition to renewable energy. The deal, which was signed by more than 190 countries, includes provisions for financial support to developing nations facing the worst impacts of climate change. Negotiators praised the agreement as a significant step forward, though environmental groups criticized it for not going far enough to limit global temperature rise to 1.5 degrees Celsius. The conference, held in Dubai, was attended by over 70,000 participants including heads of state, business leaders, and civil society representatives. Implementation mechanisms will be reviewed annually."
    },
    {
        "title": "Researchers Discover New Species of Deep Sea Fish in Pacific Ocean",
        "text": "Marine biologists from the Scripps Institution of Oceanography have discovered a new species of fish living at extreme depths in the Pacific Ocean. The fish, which belongs to the snailfish family, was found at depths of more than 8,000 meters in the Atacama Trench off the coast of South America. The discovery was made using remotely operated underwater vehicles equipped with high-definition cameras and sample collection equipment. Scientists said the new species has developed remarkable adaptations to survive in the high-pressure, low-temperature environment of the deep ocean. The fish appears to feed on small crustaceans and has a transparent body that allows its internal organs to be seen. The discovery highlights how much of the deep ocean remains unexplored."
    },
    {
        "title": "Stock Market Reaches Record High Amid Strong Corporate Earnings",
        "text": "Wall Street indices surged to record highs on Friday as strong corporate earnings reports boosted investor confidence in the strength of the economy. The S&P 500 index rose 1.8 percent to close at an all-time high of 5,248 points, while the Dow Jones Industrial Average gained 487 points. Technology companies led the rally, with several major firms reporting quarterly profits that exceeded analyst expectations. Market analysts attributed the gains to better-than-expected results from companies in the technology, healthcare, and consumer discretionary sectors. Trading volume was above average as institutional investors repositioned their portfolios following the earnings season. Federal Reserve officials signaled that interest rates could begin to decline later in the year if inflation continues to moderate."
    }
]

FAKE_NEWS = [
    {
        "title": "BREAKING: Scientists Discover Cure for ALL Diseases Using Common Kitchen Ingredient",
        "text": "SHOCKING REVELATION: Scientists at a secret government laboratory have discovered that a common kitchen ingredient can cure all known diseases including cancer, diabetes, HIV, and COVID-19. The miracle cure has been suppressed by Big Pharma for decades because it would eliminate their trillion-dollar drug industry. A whistleblower who worked at a major pharmaceutical company has come forward with documents proving that executives knew about this cure since the 1970s but chose to hide it from the public. The cure involves taking two tablespoons of baking soda mixed with apple cider vinegar every morning. Hollywood celebrities and politicians have been using this secret cure for years while the public suffers needlessly. SHARE THIS BEFORE IT GETS TAKEN DOWN! The government is trying to suppress this information because it threatens their control over the population. Doctors don't want you to know this secret!"
    },
    {
        "title": "EXCLUSIVE: Hillary Clinton Arrested at Airport with Millions in Cash",
        "text": "Sources close to the Trump administration confirm that Hillary Clinton was arrested at JFK International Airport yesterday while attempting to flee the country with millions of dollars in cash. The arrest came after investigators discovered evidence linking her to a massive corruption scheme involving foreign governments. The mainstream media is completely blacklisting this story because they are complicit in the cover-up. Clinton was reportedly caught with 47 million dollars in cash stuffed into suitcases and was carrying a fake passport. President Trump tweeted about the arrest but his tweet was immediately deleted by Twitter in an act of obvious censorship. Clinton's arrest is just the beginning of the Great Awakening that patriots have been predicting for years. Stay tuned for more updates as the Deep State begins to crumble!"
    },
    {
        "title": "COVID-19 Vaccine Contains Microchips That Allow Bill Gates to Track You",
        "text": "The truth the mainstream media refuses to tell you: COVID-19 vaccines contain microscopic tracking chips developed by Bill Gates and Microsoft that allow the government to monitor your every move. This information comes from anonymous doctors who are risking their lives to reveal the truth. The chips are activated by 5G towers, which is why the telecom industry was pushing so hard to install 5G infrastructure during the pandemic. Multiple patients have reported that metal objects stick to the vaccination site, proving the presence of the microchip. The globalist elite planned this plandemic years in advance as a way to implement their New World Order agenda. Real patriots who refuse the vaccine are being targeted by government agents. The FDA approved the vaccine without proper testing because they are controlled by big pharmaceutical companies. Wake up sheeple before it is too late!"
    },
    {
        "title": "Scientists Confirm Earth is Actually Flat: NASA has been LYING for Decades",
        "text": "Independent scientists have finally proved what flat earthers have been saying for years: the Earth is flat and NASA has been lying to the public for decades. A group of researchers using specially modified cameras and laser measurements have definitively proved that the curvature of the Earth does not exist. NASA receives billions of taxpayer dollars every year to maintain the lie of a spherical earth. All the photos of Earth from space are CGI created by Hollywood special effects artists employed by NASA. Pilots, ship captains, and military personnel who dare to speak the truth are immediately silenced and fired. The globalist conspiracy to hide the true flat nature of our world goes back centuries and was designed to keep people from discovering the truth about the dome that covers our flat earth. Share this with everyone you know before this post gets censored!"
    },
    {
        "title": "Secret Chemtrails Program Exposed: Government Spraying Mind Control Chemicals",
        "text": "A high-level government insider has leaked classified documents proving that the chemtrails you see in the sky are actually mind-control chemicals being sprayed by the government to keep the population docile and obedient. The program, code-named Operation Sky Shepherd, has been running since the 1980s and involves hundreds of specially modified aircraft. The chemicals being sprayed include barium, strontium, and experimental psychoactive compounds that lower IQ and suppress independent thought. This explains why the public is so blind to what is really happening around them. Scientists who have tried to analyze the chemicals have been threatened and several have mysteriously died. The only way to protect yourself is to wear an N95 mask outdoors and install special filters in your home. Patriots must resist this chemical assault on our minds and freedom!"
    },
    {
        "title": "URGENT: 5G Towers Are Actually Weapons Designed to Kill People",
        "text": "The sinister truth about 5G technology has finally been revealed by a team of brave independent researchers. The 5G towers being installed across America are not for improved cellular service - they are directed energy weapons designed to selectively kill people who resist the New World Order. Leaked Pentagon documents show that 5G frequencies can be focused to cause cancer, infertility, and sudden cardiac arrest in targeted individuals. This explains the mysterious deaths of several prominent truth-tellers in the past year. The Chinese government helped design the technology as part of a plan to weaken Western populations before an invasion. Local governments that have tried to ban 5G towers have been threatened by federal agents. The only way to protect yourself and your family is to surround your home with aluminum foil and avoid all contact with 5G signals. Spread this information before it disappears!"
    },
    {
        "title": "SHOCKING: Democrats Installing Voting Machines That Switch Republican Votes",
        "text": "Evidence has emerged proving that Democrat operatives have been systematically programming voting machines in key swing states to switch Republican votes to Democrat votes. A computer security expert who examined the machines said they contain hidden code that activates on election day to change results. Multiple whistleblowers from inside the election administration offices have come forward with proof of the massive fraud. The mainstream media refuses to cover this story because they want Democrats to win and destroy America. Patriot groups in several states have filed lawsuits challenging the fraudulent results. Foreign intelligence agencies are also involved in the scheme, providing funding and technical expertise. True Americans must stand up and demand paper ballots and hand counting to stop this unprecedented theft of our democracy. Share this before the deep state censors it!"
    },
    {
        "title": "Doctors Confirm: Drinking Bleach Kills All Viruses and Cures Cancer",
        "text": "In a shocking revelation that Big Pharma is desperately trying to suppress, a group of independent doctors has confirmed that drinking diluted bleach solutions can cure virtually all diseases including cancer, HIV, and COVID-19. The treatment, which involves mixing household bleach with water and drinking small amounts each day, reportedly works by killing all viruses and bacteria in the body. Thousands of people in South America have already been cured using this method, but the mainstream media refuses to cover it because pharmaceutical companies stand to lose billions. One doctor who has been treating patients with bleach solutions says he has never seen such remarkable results in his 30 years of practice. The FDA is trying to ban this information and has already sent threats to websites that promote it. Do your own research and try this miracle cure before it gets suppressed forever!"
    },
    {
        "title": "EXCLUSIVE: Secret Underground Cities Where Elites Will Survive World War 3",
        "text": "Classified documents obtained by this outlet reveal that the global elite have been secretly building massive underground cities equipped with everything needed to survive for decades after World War 3. The bunkers, located beneath major cities and rural areas across America and Europe, can house thousands of people and include hospitals, farms, and luxury amenities. The construction has been funded using black budget money siphoned from military budgets. While ordinary Americans will be left to die in the coming nuclear war, politicians, celebrities, and billionaires will retreat to their underground palaces. The war is being deliberately orchestrated by the military-industrial complex to reduce the global population and make the survivors easier to control. Several construction workers who revealed information about the bunkers have mysteriously disappeared. Patriots must prepare now for the coming collapse of civilization as we know it!"
    },
    {
        "title": "George Soros Paying Thousands of Actors to Protest at Rallies",
        "text": "Explosive new evidence has surfaced proving that billionaire George Soros has been paying thousands of professional actors and activists to attend political protests and create the illusion of mass opposition to conservative policies. Receipts obtained by a patriot journalist show payments of up to 1,500 dollars per person per day to attend rallies and carry pre-printed signs. The operation is run through a network of shell companies designed to hide Soros's involvement. Many of the protesters are bused in from other states and don't even know what they are supposedly protesting about. This proves that the resistance movement is completely artificial and manufactured by globalist elites who want to destroy America. Real Americans who support traditional values are being silenced while paid actors dominate television coverage. The truth is coming out and patriots will not be silenced much longer!"
    },
    {
        "title": "BOMBSHELL: Moon Landing Was Staged in Hollywood by Stanley Kubrick",
        "text": "Newly discovered documents and testimony from a former NASA contractor prove once and for all that the 1969 Apollo moon landing was entirely staged in a Hollywood studio by director Stanley Kubrick. The documents show that NASA hired Kubrick after the success of 2001: A Space Odyssey because they knew they could not actually land on the moon with the technology available at the time. The entire space race was a propaganda operation to convince the American public that the United States was ahead of the Soviet Union. Kubrick allegedly confessed to the deception in a secret interview filmed just before his death but the recording has been suppressed by the government. Multiple NASA employees who threatened to come forward with the truth have died under mysterious circumstances. The moon rocks brought back from the supposed missions were actually volcanic rocks from Iceland. Wake up to the biggest lie in human history!"
    },
    {
        "title": "SECRET: Fluoride in Water is Actually a Population Control Chemical",
        "text": "The disturbing truth about water fluoridation has finally been exposed by a brave scientist who risked her career to reveal that fluoride is not added to water to protect teeth but is actually a population control chemical designed to lower fertility rates and make people more compliant. Documents from the 1950s show that the government began adding fluoride to water after discovering its effects on the human endocrine system. Fluoride accumulates in the pineal gland of the brain and suppresses spiritual and psychic abilities that the elite want to prevent ordinary people from developing. Countries that have removed fluoride from their water have seen dramatic improvements in IQ scores and birth rates. The dental industry benefits financially from fluoride treatment, which explains why they push fluoridation so aggressively. Filter your water immediately and share this information with everyone you care about before the government scrubs it from the internet!"
    }
]

# ---------------------------------------------------------------------------
# Build DataFrames
# ---------------------------------------------------------------------------
print("Generating synthetic sample dataset…")

fake_rows = []
for i, article in enumerate(FAKE_NEWS):
    for j in range(20):   # Repeat each article 20 times with slight variations
        fake_rows.append({
            "title":   article["title"],
            "text":    article["text"] + f" [variant {j}]",
            "subject": random.choice(["politics", "News", "Government News"]),
            "date":    f"January {random.randint(1,28)}, 2023",
        })

true_rows = []
for i, article in enumerate(REAL_NEWS):
    for j in range(20):
        true_rows.append({
            "title":   article["title"],
            "text":    article["text"] + f" [variant {j}]",
            "subject": random.choice(["politicsNews", "worldnews", "science"]),
            "date":    f"January {random.randint(1,28)}, 2023",
        })

# ---------------------------------------------------------------------------
# Save CSVs
# ---------------------------------------------------------------------------
dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset")
os.makedirs(dataset_dir, exist_ok=True)

fake_df = pd.DataFrame(fake_rows)
true_df = pd.DataFrame(true_rows)

fake_csv = os.path.join(dataset_dir, "Fake.csv")
true_csv = os.path.join(dataset_dir, "True.csv")

fake_df.to_csv(fake_csv, index=False)
true_df.to_csv(true_csv, index=False)

print(f"[OK] Fake.csv created: {len(fake_df)} rows -> {fake_csv}")
print(f"[OK] True.csv created: {len(true_df)} rows -> {true_csv}")
print()
print("[NOTE] This is a SYNTHETIC dataset for demonstration only.")
print("   For production accuracy (98%+), use the real Kaggle dataset:")
print("   https://www.kaggle.com/clmentbisaillon/fake-and-real-news-dataset")
print()
print("Now run: python train_model.py")
