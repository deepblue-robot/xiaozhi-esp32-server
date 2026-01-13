package xiaozhi.modules.merchant;


import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;

import java.util.Map;

public interface MerchantService extends BaseService<MerchantEntity> {


    public PageData<MerchantEntity> merchantPage(Map<String, Object> params);

}
