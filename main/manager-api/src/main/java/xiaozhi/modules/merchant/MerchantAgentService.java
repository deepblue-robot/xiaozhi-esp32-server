package xiaozhi.modules.merchant;

import xiaozhi.common.service.BaseService;

import java.util.List;

public interface MerchantAgentService extends BaseService<MerchantAgentEntity> {

    public List<MerchantAgentEntity> getMerchantAgentList(Long merchantId);

}
