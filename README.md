# IMC-Prosperity-2023-Stanford-Cardinal

Stanford Cardinal's algorithms in IMC Prosperity 2023! 
#### Final Rank: 2nd of 7007 teams

## Stanford Cardinal team:

Shubham Anand Jain (Twitter: https://twitter.com/Kimi5407, LinkedIn: https://www.linkedin.com/in/sa-jain/)

Konstantin Miagkov

Parth Dodhia

## Round-wise details

#### Round 1

In this round, we worked on pearls and bananas separately. For pearls, we realized that they had a stable price of around 10,000, but there were times when the best bid was 10,002 and the best ask was 9,998. Additionally, there were trades even at -5, -4, +4 and +5 of the mean price (10k), which meant that all we had to do for pearls was market-take and market-make around 10k.

For bananas, we ran a linear regression on the last few timesteps of banana prices to predict the next price. Using this to market-take worked reasonably, and market-making along with market-taking worked quite well. We tried to implement LR-on-the-fly, but this didn't work as well (and with the Lambda error bugs that were prevalent through the competition, it was for the best to skip this approach). We noticed that the banana trends were linear-ish across days (ie, day 2 was more similar to day 1 in LR coefficients than day -1 and so on), which could give an additional boost in PnL.

The manual trading was straightforward in this round. Based on the results of Round 1, we were in 9th place.

#### Round 2

Unfortunately, both me and Konstantin were travelling/very busy during the next couple of rounds, so it was a bit harder to try things in Rounds 2-4. For the Coconuts/Pina Coladas, Konstantin wrote up code to perform pair-trading (arbitraging pina colada - 15/8 * coconut); something else we tried was momentum-based trading, but this didn't give a PnL as high as pair-trading, so we mostly submitted the first code we came up with.

For the manual round, we submitted a guess of 9,777 based on a simulation. This was good enough to net us some profit, with the median price of the bottom 50% being 9,685. Shockingly, we got a score of below -120k in the algorithmic trading in this round, which dropped us from 9th place to... 926th place!!!

#### Round 3

After the shock of dropping to an extremely low rank, we decided to not participate in Prosperity anymore. Still, Konstantin wrote some code for Berries and Diving Gear, which seemed to work reasonably. The ideas were as follows: For berries, he hardcoded some values of the curve (buy at timestamp 350k, sell at 500k, either buy or sell at 750k depending on the overall day's trend). For diving gear, he noticed that Dolphin sightings would increase or decrease by a huge amount if there was a true signal; a small change such as +-2 from the last dolphin sighting was very likely noise.

For the manual trading, I decided to enter 9,959 after a bit of eyeballing, which was close to the optimal score of 9,969. Our algorithm also worked extremely well this round, propelling us from 926th to 60th place (we had the overall highest score this round, based on https://jmerle.github.io/imc-prosperity-leaderboard/). Looking at these results, my suspicion grew about our Round 2 algorithm, and I asked the moderators once again for our logs; it turned out that our algorithm was actually judged incorrectly! Therefore, though we were officially 60th place, we knew that we were 3rd place at the moment in reality.

#### Round 4

Once we realized that we actually had a fighting chance (and were not on flights anymore), we spent more time actually working on our algorithms compared to the last 2 rounds. For the Picnic basket group, we decided to use the same pair trading strategy, assuming that the basket had a premium of 375$ attached to it (ie, arbitraging picnic basket - 4 * dip - 2 * baguette - ukulele - 375), and fine-tune this. I ended up writing a backtester that helped us test all of our strategies by using the run function (before, we were only testing via separate simulations via iterating over past data, which was annoying to change in two places.)

For the manual trading round, we found that if the stock moves $x$% and if we invest $y$%, the output function would be $75xy-90y^2$, which would put the optimal $y$ value at $y = 2.5x/6$. Using this idea, we simply individually bet on the amount we thought each stock would move, invested that much, and iterated a bit. We ended up investing about 100% of our capital.

After Round 4, we jumped to Rank 5 from Rank 60 (though we knew we actually went from Rank 3 -> 5). Our manual trading score was 75k, whereas the best score we heard was around 115k; our algorithm score was 175k, which was a bit lower than expected. We had an outside shot at winning; the difference between us and the top team was only 30k, but between us and the 10th team was a 100k! 

#### Round 5

For Round 5, my first order of business was to extend our backtester to handle market orders, while Konstantin ran some preliminary data analysis on the market order trades. We ended up implementing the following changes:

1. We realized that in the Picnic Basket bucket, Picnic Basket always had heavily positive PnL; this meant that the price of all the products were a leading indicator for the future price of picnic baskets, which made sense. Therefore, we decided to only trade Picnic Baskets on the signal of (picnic basket - 4 * dip - 2 * baguette - ukulele - 375).

2. We realized Olivia bought at the lowest point and sold at the highest point, so we used her exclusively to trade Ukuleles. For berries, her signal was used to augment our existing code and made our algorithm slightly better.

3. We did the same thing as point 1 for pina coladas and coconuts (ie, only trade pina coladas); this was not necessarily the best choice or a perfectly justified one (since we did not have a great increase in results from doing this), but it was a choice we made.

We further decided to never trade Dip, Baguettes or Coconuts. Some more ideas we considered (but could not get to work reliably) were:

1. Perform market making on dip, due to it having a large spread and low price deviation (except for a sharp dip at some point); while this performed very well on average, the sharp dip lost us a lot of money, and therefore we couldn't get this to work in a short amount of time.

2. Use Camilla as a signal for berries: We noticed that Camilla would constantly make profits, so she might have been a good signal for berries; however, she also got a lot of edge (great deals on the correct side of the spread), and we could not emulate her success better than how our own algorithm + Olivia's was performing.

3. Use some sort of momentum based ideas for Baguettes: we noticed that Baguettes usually go on a strong upward or downward run, which allowed momemtum-based strategies to work well. We were able to make a consistent 5-20k PnL on one of our signals, but changing the parameters slightly changed these numbers from -30k to 50k. We ended up not taking the risk here, and removed this signal.

#### Final results

After all was said and done, we ended up in... 2nd place. While this is a good result, this competition had announced a prize only for top 1, so it hurt a bit being 2nd... Also, the AWS Lambda errors left a bit of a sour taste in our mouths.

But when all was said and done, this was a fun competition in which we got to work on some cool ideas; so thank you to all of the people behind Prosperity, and everyone who participated - it was exciting participating alongside yall! :) 

PS - IMC reached out to send us a "present".. I'm curious what it is :D
