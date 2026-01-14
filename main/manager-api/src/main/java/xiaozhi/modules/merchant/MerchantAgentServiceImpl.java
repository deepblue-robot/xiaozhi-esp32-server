package xiaozhi.modules.merchant;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Service;
import xiaozhi.common.service.impl.BaseServiceImpl;

import java.util.List;

@Service
public class MerchantAgentServiceImpl extends BaseServiceImpl<MerchantAgentMapper, MerchantAgentEntity> implements MerchantAgentService {

    @Resource
    private MerchantAgentMapper merchantAgentMapper;


    @Override
    public List<MerchantAgentEntity> getMerchantAgentList(Long merchantId) {
        QueryWrapper<MerchantAgentEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("merchant_id", merchantId);
        return merchantAgentMapper.selectList(wrapper);
    }
}
