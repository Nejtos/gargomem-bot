from bot.game.entities.base import GameEntity


class Items(GameEntity):
    async def is_shop_open(self) -> bool:
        return await self._evaluate("""
            () => !!(window.Engine && window.Engine.shop && typeof window.Engine.shop.greatMerchant === "function")
        """)

    async def close_shop(self):
        return await self._evaluate(f"""() => window.Engine.shop.close()""")

    async def finalize_basket(self):
        return await self._evaluate(f"""() => window.Engine.shop.basket.finalize()""")

    async def quick_sell_items(self, index):
        return await self._evaluate(f"() => {{ window.Engine.shop.greatMerchant({index}) }}")

    async def find_and_buy_item(self, item_id):
        return await self._evaluate(f"""
            () => {{
                let item = Object.values(window.Engine.shop.items).find(i => i.id == '{item_id}');
                if(item) {{
                    window.Engine.shop.basket.buyItem(item);
                }}
            }};
        """)

    async def locate_and_collect_item(self):
        return await self._evaluate("""
            (function() {
                const {x: t, y: e} = Engine.hero.d, i = Engine.map.groundItems.getGroundItemOnPosition(t, e);
                i.length > 0 && _g("takeitem&id=" + i[0].id);
                const n = Engine.npcs.getRenewableNpcByPosition(t, e);
                n && Engine.hero.sendRequestToTalk(n.d.id)
            })();
        """)

    async def open_crafting(self):
        return await self._evaluate("""() => window.Engine.crafting.triggerOpen()""")

    async def close_crafting(self):
        return await self._evaluate("""() => window.Engine.crafting.triggerClose()""")

    async def fetch_recipes(self):
        return await self._evaluate("""
            (() => {
                const recipes = window.Engine.crafting.recipes.recipes;
                if (!recipes) return null;
                const active = Object.entries(recipes)
                    .find(([id, data]) => data.enabled === 1);
                if (!active) return null;
                const [id, data] = active;
                return { id: parseInt(id), name: data.name };
            })();
        """)

    async def select_recipe(self, recipe_id):
        return await self._evaluate(f"""
        () => window.Engine.crafting.recipes.showRecipe({recipe_id})
    """)

    async def confirm_selected_recipe(self, recipe_id):
        return await self._evaluate(f"""
        () => window.Engine.crafting.recipes.confirmUseRecipe({recipe_id})
    """)

    async def accept_recipe(self):
        return await self._evaluate(f"""
        () => window.Engine.hotKeys.checkCanAcceptAlert()
    """)

    async def fetch_barter_data(self):
        return await self._evaluate("""
            (() => {
                    const categories = window.Engine?.barter?.allCategories;
                    if (!categories) return null;
                    for (const catKey in categories) {
                        const catItems = categories[catKey];
                        if (!Array.isArray(catItems)) continue;
                        for (const item of catItems) {
                            if (item.maxAmount === 1) {
                                return {
                                    offerId: item.affectedId,
                                    itemId: item.id,
                                    category: item.category
                                };
                            }
                        }
                    }
                    return null;
                })();
            """)

    async def find_barter_offer(self, offer_id):
        return await self._evaluate(f"""
            () => {{
                const offerList = window.Engine.barter.createOneOfferOnList(window.Engine.barter.allParseOffers[{offer_id}]);
                if (offerList && offerList[0]) {{
                    window.Engine.barter.recipeClick(offerList[0], offerList[0]);
                }}
            }}
        """)

    async def do_barter(self, item_id):
        return await self._evaluate(f"() => window.Engine.barter.doBarter({item_id})")

    async def finish_barter(self):
        return await self._evaluate("() => window.Engine.barter.close()")

    async def equip_item(self, item_id):
        return await self._evaluate(f"""() => _g("moveitem&st=1&id={item_id}")""")

    async def use_potion(self, potion_id):
        return await self._evaluate(f"""(function() {{ _g("moveitem&st=1&id={potion_id}")}})();""")

    async def get_bags_with_items_data(self):
        return await self._evaluate("""
            () => {
                return (window.Engine.bags || [])
                    .map((b, index) => ({ b, index }))
                    .filter(({ index }) => index < 3)
                    .filter(({ b }) => b && Array.isArray(b) && b[2] !== 1195874772)
                    .map(({ b: [max_size, actual_items_amount, location], index }) => ({
                        index,
                        max_size,
                        actual_items_amount,
                        location
                    }))
                    .filter(b => b.actual_items_amount > 0);
            }
        """)
