import BaseLayout from "../../components/BasedLayout.vue"
import List from "./List.vue"
//@ts-ignore
import Edit from "./Create.vue"

export default {
    path: '/configs/',
    component: BaseLayout,
    children: [
        { path: '', component: List },
        { path: 'create/', component: Edit },
    ]
}
