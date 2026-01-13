package xiaozhi.modules.merchant;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import jakarta.annotation.Resource;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;
import xiaozhi.common.page.PageData;
import xiaozhi.common.service.impl.BaseServiceImpl;

import java.util.Map;


@Service
@AllArgsConstructor
public class MerchantServiceImpl extends BaseServiceImpl<MerchantMapper, MerchantEntity>  implements MerchantService {


    @Resource
    private MerchantMapper merchantMapper;


    @Override
    public PageData<MerchantEntity> merchantPage(Map<String, Object> params) {
        IPage<MerchantEntity> page = merchantMapper.selectPage(
                getPage(params, "id", true),
                new QueryWrapper<>());
        return new PageData<>(page.getRecords(), page.getTotal());
    }

}
