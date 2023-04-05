from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import collections
from collections import defaultdict
import random
import math
import copy
import numpy as np

empty_dict = {'PEARLS' : 0, 'BANANAS' : 0, 'COCONUTS' : 0, 'PINA_COLADAS' : 0, 'BERRIES' : 0, 'DIVING_GEAR' : 0, 'DIP' : 0, 'BAGUETTE': 0, 'UKULELE' : 0, 'PICNIC_BASKET' : 0}


def def_value():
    return copy.deepcopy(empty_dict)

INF = int(1e9)

class Trader:

    position = copy.deepcopy(empty_dict)
    POSITION_LIMIT = {'PEARLS' : 20, 'BANANAS' : 20, 'COCONUTS' : 600, 'PINA_COLADAS' : 300, 'BERRIES' : 250, 'DIVING_GEAR' : 50, 'DIP' : 300, 'BAGUETTE': 150, 'UKULELE' : 70, 'PICNIC_BASKET' : 70}
    volume_traded = copy.deepcopy(empty_dict)

    person_position = defaultdict(def_value)
    person_actvalof_position = defaultdict(def_value)

    cpnl = defaultdict(lambda : 0)
    bananas_cache = []
    coconuts_cache = []
    bananas_dim = 4
    coconuts_dim = 3
    steps = 0
    last_dolphins = -1
    buy_gear = False
    sell_gear = False
    buy_berries = False
    sell_berries = False
    close_berries = False
    last_dg_price = 0
    start_berries = 0
    first_berries = 0
    cont_buy_basket_unfill = 0
    cont_sell_basket_unfill = 0
    
    halflife_diff = 5
    alpha_diff = 1 - np.exp(-np.log(2)/halflife_diff)

    halflife_price = 5
    alpha_price = 1 - np.exp(-np.log(2)/halflife_price)

    halflife_price_dip = 20
    alpha_price_dip = 1 - np.exp(-np.log(2)/halflife_price_dip)
    
    begin_diff_dip = -INF
    begin_diff_bag = -INF
    begin_bag_price = -INF
    begin_dip_price = -INF

    std = 25
    basket_std = 117

    def calc_next_price_bananas(self):
        # bananas cache stores price from 1 day ago, current day resp
        # by price, here we mean mid price

        coef = [-0.01869561,  0.0455032 ,  0.16316049,  0.8090892]
        intercept = 4.481696494462085
        nxt_price = intercept
        for i, val in enumerate(self.bananas_cache):
            nxt_price += val * coef[i]

        return int(round(nxt_price))

    def values_extract(self, order_dict, buy=0):
        tot_vol = 0
        best_val = -1
        mxvol = -1

        for ask, vol in order_dict.items():
            if(buy==0):
                vol *= -1
            tot_vol += vol
            if tot_vol > mxvol:
                mxvol = vol
                best_val = ask
        
        return tot_vol, best_val
    


    def compute_orders_pearls(self, product, order_depth, acc_bid, acc_ask):
        orders: list[Order] = []

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        sell_vol, best_sell_pr = self.values_extract(osell)
        buy_vol, best_buy_pr = self.values_extract(obuy, 1)

        cpos = self.position[product]

        mx_with_buy = -1

        for ask, vol in osell.items():
            if ((ask < acc_bid) or ((self.position[product]<0) and (ask == acc_bid))) and cpos < self.POSITION_LIMIT['PEARLS']:
                mx_with_buy = max(mx_with_buy, ask)
                order_for = min(-vol, self.POSITION_LIMIT['PEARLS'] - cpos)
                cpos += order_for
                assert(order_for >= 0)
                orders.append(Order(product, ask, order_for))

        mprice_actual = (best_sell_pr + best_buy_pr)/2
        mprice_ours = (acc_bid+acc_ask)/2

        undercut_buy = best_buy_pr + 1
        undercut_sell = best_sell_pr - 1

        bid_pr = min(undercut_buy, acc_bid-1) # we will shift this by 1 to beat this price
        sell_pr = max(undercut_sell, acc_ask+1)

        if (cpos < self.POSITION_LIMIT['PEARLS']) and (self.position[product] < 0):
            num = min(40, self.POSITION_LIMIT['PEARLS'] - cpos)
            orders.append(Order(product, min(undercut_buy + 1, acc_bid-1), num))
            cpos += num

        if (cpos < self.POSITION_LIMIT['PEARLS']) and (self.position[product] > 15):
            num = min(40, self.POSITION_LIMIT['PEARLS'] - cpos)
            orders.append(Order(product, min(undercut_buy - 1, acc_bid-1), num))
            cpos += num

        if cpos < self.POSITION_LIMIT['PEARLS']:
            num = min(40, self.POSITION_LIMIT['PEARLS'] - cpos)
            orders.append(Order(product, bid_pr, num))
            cpos += num
        
        cpos = self.position[product]

        for bid, vol in obuy.items():
            if ((bid > acc_ask) or ((self.position[product]>0) and (bid == acc_ask))) and cpos > -self.POSITION_LIMIT['PEARLS']:
                order_for = max(-vol, -self.POSITION_LIMIT['PEARLS']-cpos)
                # order_for is a negative number denoting how much we will sell
                cpos += order_for
                assert(order_for <= 0)
                orders.append(Order(product, bid, order_for))

        if (cpos > -self.POSITION_LIMIT['PEARLS']) and (self.position[product] > 0):
            num = max(-40, -self.POSITION_LIMIT['PEARLS']-cpos)
            orders.append(Order(product, max(undercut_sell-1, acc_ask+1), num))
            cpos += num

        if (cpos > -self.POSITION_LIMIT['PEARLS']) and (self.position[product] < -15):
            num = max(-40, -self.POSITION_LIMIT['PEARLS']-cpos)
            orders.append(Order(product, max(undercut_sell+1, acc_ask+1), num))
            cpos += num

        if cpos > -self.POSITION_LIMIT['PEARLS']:
            num = max(-40, -self.POSITION_LIMIT['PEARLS']-cpos)
            orders.append(Order(product, sell_pr, num))
            cpos += num

        return orders


    def compute_orders_regression(self, product, order_depth, acc_bid, acc_ask, LIMIT):
        orders: list[Order] = []

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        sell_vol, best_sell_pr = self.values_extract(osell)
        buy_vol, best_buy_pr = self.values_extract(obuy, 1)

        cpos = self.position[product]

        for ask, vol in osell.items():
            if ((ask <= acc_bid) or ((self.position[product]<0) and (ask == acc_bid+1))) and cpos < LIMIT:
                order_for = min(-vol, LIMIT - cpos)
                cpos += order_for
                assert(order_for >= 0)
                orders.append(Order(product, ask, order_for))

        undercut_buy = best_buy_pr + 1
        undercut_sell = best_sell_pr - 1

        bid_pr = min(undercut_buy, acc_bid) # we will shift this by 1 to beat this price
        sell_pr = max(undercut_sell, acc_ask)

        if cpos < LIMIT:
            num = LIMIT - cpos
            orders.append(Order(product, bid_pr, num))
            cpos += num
        
        cpos = self.position[product]
        

        for bid, vol in obuy.items():
            if ((bid >= acc_ask) or ((self.position[product]>0) and (bid+1 == acc_ask))) and cpos > -LIMIT:
                order_for = max(-vol, -LIMIT-cpos)
                # order_for is a negative number denoting how much we will sell
                cpos += order_for
                assert(order_for <= 0)
                orders.append(Order(product, bid, order_for))

        if cpos > -LIMIT:
            num = -LIMIT-cpos
            orders.append(Order(product, sell_pr, num))
            cpos += num

        return orders
    
    def compute_orders_c_and_pc(self, order_depth):
        orders = {'COCONUTS' : [], 'PINA_COLADAS' : []}
        prods = ['COCONUTS', 'PINA_COLADAS']
        coef = 1.875
        osell, obuy, best_sell, best_buy, worst_sell, worst_buy, mid_price, vol_buy, vol_sell = {}, {}, {}, {}, {}, {}, {}, {}, {}
        for p in prods:
            osell[p] = collections.OrderedDict(sorted(order_depth[p].sell_orders.items()))
            obuy[p] = collections.OrderedDict(sorted(order_depth[p].buy_orders.items(), reverse=True))

            best_sell[p] = next(iter(osell[p]))
            best_buy[p] = next(iter(obuy[p]))

            worst_sell[p] = next(reversed(osell[p]))
            worst_buy[p] = next(reversed(obuy[p]))

            mid_price[p] = (best_sell[p] + best_buy[p])/2
            vol_buy[p], vol_sell[p] = 0, 0
            for price, vol in obuy[p].items():
                vol_buy[p] += vol 
                if vol_buy[p] >= self.POSITION_LIMIT[p]/10:
                    break
            for price, vol in osell[p].items():
                vol_sell[p] += -vol 
                if vol_sell[p] >= self.POSITION_LIMIT[p]/10:
                    break

        res = mid_price['PINA_COLADAS'] - coef*mid_price['COCONUTS']
        # print(f'Residual std: {self.std}')
        trade_at = self.std*1
        close_at = self.std*(-0.5)

        coco_pos = self.position['COCONUTS']
        coco_neg = self.position['COCONUTS']
        put_order = 0

        if res > trade_at:
            vol = self.position['PINA_COLADAS'] + self.POSITION_LIMIT['PINA_COLADAS']
            assert(vol >= 0)
            if vol > 0:
                orders['PINA_COLADAS'].append(Order('PINA_COLADAS', worst_buy['PINA_COLADAS'], -vol))
        elif res < -trade_at:
            vol = self.POSITION_LIMIT['PINA_COLADAS'] - self.position['PINA_COLADAS']
            assert(vol >= 0)
            if vol > 0:
                orders['PINA_COLADAS'].append(Order('PINA_COLADAS', worst_sell['PINA_COLADAS'], vol))
        elif res < close_at and self.position['PINA_COLADAS'] < 0:
            vol = -self.position['PINA_COLADAS']
            assert(vol >= 0)
            if vol > 0:
                orders['PINA_COLADAS'].append(Order('PINA_COLADAS', worst_sell['PINA_COLADAS'], vol))
        elif res > -close_at and self.position['PINA_COLADAS'] > 0:
            vol = self.position['PINA_COLADAS']
            assert(vol >= 0)
            if vol > 0:
                orders['PINA_COLADAS'].append(Order('PINA_COLADAS', worst_buy['PINA_COLADAS'], -vol))

        return orders
    
    def compute_orders_basket(self, order_depth):

        orders = {'DIP' : [], 'BAGUETTE': [], 'UKULELE' : [], 'PICNIC_BASKET' : []}
        prods = ['DIP', 'BAGUETTE', 'UKULELE', 'PICNIC_BASKET']
        osell, obuy, best_sell, best_buy, worst_sell, worst_buy, mid_price, vol_buy, vol_sell = {}, {}, {}, {}, {}, {}, {}, {}, {}

        for p in prods:
            osell[p] = collections.OrderedDict(sorted(order_depth[p].sell_orders.items()))
            obuy[p] = collections.OrderedDict(sorted(order_depth[p].buy_orders.items(), reverse=True))

            best_sell[p] = next(iter(osell[p]))
            best_buy[p] = next(iter(obuy[p]))

            worst_sell[p] = next(reversed(osell[p]))
            worst_buy[p] = next(reversed(obuy[p]))

            mid_price[p] = (best_sell[p] + best_buy[p])/2
            vol_buy[p], vol_sell[p] = 0, 0
            for price, vol in obuy[p].items():
                vol_buy[p] += vol 
                if vol_buy[p] >= self.POSITION_LIMIT[p]/10:
                    break
            for price, vol in osell[p].items():
                vol_sell[p] += -vol 
                if vol_sell[p] >= self.POSITION_LIMIT[p]/10:
                    break

        res_buy = mid_price['PICNIC_BASKET'] - mid_price['DIP']*4 - mid_price['BAGUETTE']*2 - mid_price['UKULELE'] - 375
        res_sell = mid_price['PICNIC_BASKET'] - mid_price['DIP']*4 - mid_price['BAGUETTE']*2 - mid_price['UKULELE'] - 375

        trade_at = self.basket_std*0.5
        close_at = self.basket_std*(-1000)

        pb_pos = self.position['PICNIC_BASKET']
        pb_neg = self.position['PICNIC_BASKET']

        uku_pos = self.position['UKULELE']
        uku_neg = self.position['UKULELE']


        basket_buy_sig = 0
        basket_sell_sig = 0

        if self.position['PICNIC_BASKET'] == self.POSITION_LIMIT['PICNIC_BASKET']:
            self.cont_buy_basket_unfill = 0
        if self.position['PICNIC_BASKET'] == -self.POSITION_LIMIT['PICNIC_BASKET']:
            self.cont_sell_basket_unfill = 0

        do_bask = 0

        if res_sell > trade_at:
            vol = self.position['PICNIC_BASKET'] + self.POSITION_LIMIT['PICNIC_BASKET']
            self.cont_buy_basket_unfill = 0 # no need to buy rn
            assert(vol >= 0)
            if vol > 0:
                do_bask = 1
                basket_sell_sig = 1
                orders['PICNIC_BASKET'].append(Order('PICNIC_BASKET', worst_buy['PICNIC_BASKET'], -vol)) 
                self.cont_sell_basket_unfill += 2
                pb_neg -= vol
                #uku_pos += vol
        elif res_buy < -trade_at:
            vol = self.POSITION_LIMIT['PICNIC_BASKET'] - self.position['PICNIC_BASKET']
            self.cont_sell_basket_unfill = 0 # no need to sell rn
            assert(vol >= 0)
            if vol > 0:
                do_bask = 1
                basket_buy_sig = 1
                orders['PICNIC_BASKET'].append(Order('PICNIC_BASKET', worst_sell['PICNIC_BASKET'], vol))
                self.cont_buy_basket_unfill += 2
                pb_pos += vol

        if int(round(self.person_position['Olivia']['UKULELE'])) > 0:

            val_ord = self.POSITION_LIMIT['UKULELE'] - uku_pos
            if val_ord > 0:
                orders['UKULELE'].append(Order('UKULELE', worst_sell['UKULELE'], val_ord))
        if int(round(self.person_position['Olivia']['UKULELE'])) < 0:

            val_ord = -(self.POSITION_LIMIT['UKULELE'] + uku_neg)
            if val_ord < 0:
                orders['UKULELE'].append(Order('UKULELE', worst_buy['UKULELE'], val_ord))

        return orders
    
    def compute_orders_dg(self, order_depth, observations):
        orders = {'DIVING_GEAR' : []}
        prods = ['DIVING_GEAR']
        osell, obuy, best_sell, best_buy, worst_sell, worst_buy, mid_price, vol_buy, vol_sell = {}, {}, {}, {}, {}, {}, {}, {}, {}
        for p in prods:
            osell[p] = collections.OrderedDict(sorted(order_depth[p].sell_orders.items()))
            obuy[p] = collections.OrderedDict(sorted(order_depth[p].buy_orders.items(), reverse=True))

            best_sell[p] = next(iter(osell[p]))
            best_buy[p] = next(iter(obuy[p]))

            worst_sell[p] = next(reversed(osell[p]))
            worst_buy[p] = next(reversed(obuy[p]))

            mid_price[p] = (best_sell[p] + best_buy[p])/2
            vol_buy[p], vol_sell[p] = 0, 0
            for price, vol in obuy[p].items():
                vol_buy[p] += vol 
            for price, vol in osell[p].items():
                vol_sell[p] += -vol 

        if self.last_dolphins != -1 and (observations['DOLPHIN_SIGHTINGS'] - self.last_dolphins > 5):
            self.buy_gear = True
        if self.last_dolphins != -1 and (observations['DOLPHIN_SIGHTINGS'] - self.last_dolphins < -5):
            self.sell_gear = True
        
        if self.buy_gear and self.position['DIVING_GEAR'] == self.POSITION_LIMIT['DIVING_GEAR']:
            self.buy_gear = False
        if self.sell_gear and self.position['DIVING_GEAR'] == -self.POSITION_LIMIT['DIVING_GEAR']:
            self.sell_gear = False

        if self.buy_gear:
            vol = self.POSITION_LIMIT['DIVING_GEAR'] - self.position['DIVING_GEAR']
            orders['DIVING_GEAR'].append(Order('DIVING_GEAR', worst_sell['DIVING_GEAR'], vol))
        if self.sell_gear:
            vol = self.position['DIVING_GEAR'] + self.POSITION_LIMIT['DIVING_GEAR']
            orders['DIVING_GEAR'].append(Order('DIVING_GEAR', worst_buy['DIVING_GEAR'], -vol))
        self.last_dolphins = observations['DOLPHIN_SIGHTINGS']

        self.last_dg_price = mid_price['DIVING_GEAR']

        return orders
    
    def compute_orders_br(self, order_depth, timestamp):
        orders = {'BERRIES' : []}
        prods = ['BERRIES']
        osell, obuy, best_sell, best_buy, worst_sell, worst_buy, mid_price, vol_buy, vol_sell = {}, {}, {}, {}, {}, {}, {}, {}, {}
        for p in prods:
            osell[p] = collections.OrderedDict(sorted(order_depth[p].sell_orders.items()))
            obuy[p] = collections.OrderedDict(sorted(order_depth[p].buy_orders.items(), reverse=True))

            best_sell[p] = next(iter(osell[p]))
            best_buy[p] = next(iter(obuy[p]))

            worst_sell[p] = next(reversed(osell[p]))
            worst_buy[p] = next(reversed(obuy[p]))

            mid_price[p] = (best_sell[p] + best_buy[p])/2
            vol_buy[p], vol_sell[p] = 0, 0
            for price, vol in obuy[p].items():
                vol_buy[p] += vol 
            for price, vol in osell[p].items():
                vol_sell[p] += -vol 

        if timestamp == 0:
            self.start_berries = mid_price['BERRIES']
        if timestamp == 350*1000:
            self.first_berries = mid_price['BERRIES']
            self.buy_berries = True
        if timestamp == 500*1000:
            self.sell_berries = True
        if timestamp == 750*1000: 
            if self.first_berries != 0 and self.start_berries != 0 and self.first_berries > self.start_berries:
                self.buy_berries = True
            elif self.first_berries == 0 or self.start_berries == 0:
                self.close_berries = True

        if int(round(self.person_position['Olivia']['BERRIES'])) > 0:
            self.buy_berries = True
            self.sell_berries = False
        if int(round(self.person_position['Olivia']['BERRIES'])) < 0:
            self.sell_berries = True
            self.buy_berries = False

        if self.buy_berries and self.position['BERRIES'] == self.POSITION_LIMIT['BERRIES']:
            self.buy_berries = False
        if self.sell_berries and self.position['BERRIES'] == -self.POSITION_LIMIT['BERRIES']:
            self.sell_berries = False
        if self.close_berries and self.position['BERRIES'] == 0:
            self.close_berries = False

        if self.buy_berries:
            vol = self.POSITION_LIMIT['BERRIES'] - self.position['BERRIES']
            orders['BERRIES'].append(Order('BERRIES', best_sell['BERRIES'], vol))
        if self.sell_berries:
            vol = self.position['BERRIES'] + self.POSITION_LIMIT['BERRIES']
            orders['BERRIES'].append(Order('BERRIES', best_buy['BERRIES'], -vol))
        if self.close_berries:
            vol = -self.position['BERRIES']
            if vol < 0:
                orders['BERRIES'].append(Order('BERRIES', best_buy['BERRIES'], vol)) 
            else:
                orders['BERRIES'].append(Order('BERRIES', best_sell['BERRIES'], vol)) 
        return orders


    def compute_orders(self, product, order_depth, acc_bid, acc_ask):

        if product == "PEARLS":
            return self.compute_orders_pearls(product, order_depth, acc_bid, acc_ask)
        if product == "BANANAS":
            return self.compute_orders_regression(product, order_depth, acc_bid, acc_ask, self.POSITION_LIMIT[product])
        
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {'PEARLS' : [], 'BANANAS' : [], 'COCONUTS' : [], 'PINA_COLADAS' : [], 'DIVING_GEAR' : [], 'BERRIES' : [], 'DIP' : [], 'BAGUETTE' : [], 'UKULELE' : [], 'PICNIC_BASKET' : []}

        # Iterate over all the keys (the available products) contained in the order dephts
        for key, val in state.position.items():
            self.position[key] = val
        print()
        for key, val in self.position.items():
            print(f'{key} position: {val}')

        assert abs(self.position.get('UKULELE', 0)) <= self.POSITION_LIMIT['UKULELE']

        timestamp = state.timestamp

        if len(self.bananas_cache) == self.bananas_dim:
            self.bananas_cache.pop(0)
        if len(self.coconuts_cache) == self.coconuts_dim:
            self.coconuts_cache.pop(0)

        _, bs_bananas = self.values_extract(collections.OrderedDict(sorted(state.order_depths['BANANAS'].sell_orders.items())))
        _, bb_bananas = self.values_extract(collections.OrderedDict(sorted(state.order_depths['BANANAS'].buy_orders.items(), reverse=True)), 1)

        self.bananas_cache.append((bs_bananas+bb_bananas)/2)

        INF = 1e9
    
        bananas_lb = -INF
        bananas_ub = INF

        if len(self.bananas_cache) == self.bananas_dim:
            bananas_lb = self.calc_next_price_bananas()-1
            bananas_ub = self.calc_next_price_bananas()+1

        pearls_lb = 10000
        pearls_ub = 10000

        # CHANGE FROM HERE

        acc_bid = {'PEARLS' : pearls_lb, 'BANANAS' : bananas_lb} # we want to buy at slightly below
        acc_ask = {'PEARLS' : pearls_ub, 'BANANAS' : bananas_ub} # we want to sell at slightly above

        self.steps += 1

        for product in state.market_trades.keys():
            for trade in state.market_trades[product]:
                if trade.buyer == trade.seller:
                    continue
                self.person_position[trade.buyer][product] = 1.5
                self.person_position[trade.seller][product] = -1.5
                self.person_actvalof_position[trade.buyer][product] += trade.quantity
                self.person_actvalof_position[trade.seller][product] += -trade.quantity

        orders = self.compute_orders_c_and_pc(state.order_depths)
        result['PINA_COLADAS'] += orders['PINA_COLADAS']
        result['COCONUTS'] += orders['COCONUTS']
        orders = self.compute_orders_dg(state.order_depths, state.observations)
        result['DIVING_GEAR'] += orders['DIVING_GEAR']
        orders = self.compute_orders_br(state.order_depths, state.timestamp)
        result['BERRIES'] += orders['BERRIES']

        orders = self.compute_orders_basket(state.order_depths)
        result['PICNIC_BASKET'] += orders['PICNIC_BASKET']
        result['DIP'] += orders['DIP']
        result['BAGUETTE'] += orders['BAGUETTE']
        result['UKULELE'] += orders['UKULELE']

        for product in ['PEARLS', 'BANANAS']:
            order_depth: OrderDepth = state.order_depths[product]
            orders = self.compute_orders(product, order_depth, acc_bid[product], acc_ask[product])
            result[product] += orders

        for product in state.own_trades.keys():
            for trade in state.own_trades[product]:
                if trade.timestamp != state.timestamp-100:
                    continue
                # print(f'We are trading {product}, {trade.buyer}, {trade.seller}, {trade.quantity}, {trade.price}')
                self.volume_traded[product] += abs(trade.quantity)
                if trade.buyer == "SUBMISSION":
                    self.cpnl[product] -= trade.quantity * trade.price
                else:
                    self.cpnl[product] += trade.quantity * trade.price

        totpnl = 0

        for product in state.order_depths.keys():
            settled_pnl = 0
            best_sell = min(state.order_depths[product].sell_orders.keys())
            best_buy = max(state.order_depths[product].buy_orders.keys())

            if self.position[product] < 0:
                settled_pnl += self.position[product] * best_buy
            else:
                settled_pnl += self.position[product] * best_sell
            totpnl += settled_pnl + self.cpnl[product]
            print(f"For product {product}, {settled_pnl + self.cpnl[product]}, {(settled_pnl+self.cpnl[product])/(self.volume_traded[product]+1e-20)}")

        for person in self.person_position.keys():
            for val in self.person_position[person].keys():
                
                if person == 'Olivia':
                    self.person_position[person][val] *= 0.995
                if person == 'Pablo':
                    self.person_position[person][val] *= 0.8
                if person == 'Camilla':
                    self.person_position[person][val] *= 0

        print(f"Timestamp {timestamp}, Total PNL ended up being {totpnl}")
        # print(f'Will trade {result}')
        print("End transmission")
                
        return result